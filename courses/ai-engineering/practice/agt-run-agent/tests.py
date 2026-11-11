from fake_llm import FakeAnthropic, reply, text, tool_use
from solution import run_agent

WEATHER = {"name": "get_weather", "description": "Weather for a city",
           "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}


def weather(inp):
    if inp["city"] == "Atlantis":
        raise ValueError("city not found")
    return f"31C in {inp['city']}"


HANDLERS = {"get_weather": weather}


def test_parallel_calls_answered_in_one_message_and_logged():
    a = tool_use("get_weather", {"city": "Lagos"}, id="t1")
    b = tool_use("get_weather", {"city": "Accra"}, id="t2")
    client = FakeAnthropic([reply(text("Checking."), a, b), reply(text("Both hot."))])
    got = run_agent(client, "Lagos and Accra?", [WEATHER], HANDLERS)
    assert got["status"] == "done" and got["text"] == "Both hot.", f"expected done / 'Both hot.', got {got!r}"
    assert got["turns"] == 2, f"expected 2 turns, got {got['turns']}"
    last = client.calls[1]["messages"][-1]
    ids = [r["tool_use_id"] for r in last["content"]]
    assert ids == ["t1", "t2"], f"both results belong in one user message, got ids {ids!r}"
    want = [{"name": "get_weather", "input": {"city": "Lagos"}, "is_error": False},
            {"name": "get_weather", "input": {"city": "Accra"}, "is_error": False}]
    assert got["tool_calls"] == want, f"expected {want!r}, got {got['tool_calls']!r}"


def test_tool_errors_and_unknown_tools_use_is_error():
    a = tool_use("get_weather", {"city": "Atlantis"}, id="t1")
    b = tool_use("launch_rocket", {}, id="t2")
    client = FakeAnthropic([reply(a, b), reply(text("Sorry."))])
    got = run_agent(client, "Go", [WEATHER], HANDLERS)
    results = client.calls[1]["messages"][-1]["content"]
    assert all(r.get("is_error") is True for r in results), f"both results should have is_error True, got {results!r}"
    assert "city not found" in results[0]["content"], "put the error message in the tool_result content"
    assert [c["is_error"] for c in got["tool_calls"]] == [True, True], "record is_error in tool_calls"


def test_pause_turn_continues_without_a_user_message():
    paused = reply(text("Still searching..."), stop_reason="pause_turn")
    client = FakeAnthropic([paused, reply(text("Found it."))])
    got = run_agent(client, "Research this", [WEATHER], HANDLERS)
    assert got["status"] == "done" and got["text"] == "Found it.", f"pause_turn should continue, got {got!r}"
    msgs = client.calls[1]["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant"], \
        f"after pause_turn, send the paused assistant turn back as is, got roles {[m['role'] for m in msgs]!r}"


def test_max_tokens_mid_tool_call_retries_with_more_room():
    cut = reply(text("Let me check"), tool_use("get_weather", {}), stop_reason="max_tokens")
    client = FakeAnthropic([cut, reply(text("Done."))])
    got = run_agent(client, "Weather?", [WEATHER], HANDLERS, max_tokens=1000)
    assert got["status"] == "done", f"expected a retry then done, got {got!r}"
    assert client.calls[1]["max_tokens"] == 2000, f"double max_tokens on retry, got {client.calls[1]['max_tokens']!r}"
    assert len(client.calls[1]["messages"]) == 1, "retry the same messages; don't append the cut-off turn"


def test_truncated_text_and_refusal_stop_immediately():
    client = FakeAnthropic([reply(text("Once upon a"), stop_reason="max_tokens")])
    got = run_agent(client, "Story", [WEATHER], HANDLERS)
    assert got["status"] == "truncated" and got["text"] == "Once upon a", f"expected truncated, got {got!r}"
    client = FakeAnthropic([reply(text(""), stop_reason="refusal")])
    got = run_agent(client, "Something harmful", [WEATHER], HANDLERS)
    assert got["status"] == "refused" and len(client.calls) == 1, f"refusal should stop with no retry, got {got!r}"


def test_turn_budget_returns_max_turns():
    script = [reply(tool_use("get_weather", {"city": "Lagos"})) for _ in range(3)]
    client = FakeAnthropic(script)
    got = run_agent(client, "Loop forever", [WEATHER], HANDLERS, max_turns=3)
    assert got["status"] == "max_turns", f"expected status 'max_turns', got {got['status']!r}"
    assert len(client.calls) == 3 and got["turns"] == 3, f"expected exactly 3 calls, got {len(client.calls)}"
    assert len(got["tool_calls"]) == 3, "tool calls made before the budget ran out should still be recorded"
