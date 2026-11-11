from fake_llm import FakeAnthropic, reply, text, tool_use
from solution import run_tool_loop

WEATHER = {"name": "get_weather", "description": "Weather for a city",
           "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}


def weather(inp):
    return f"31C in {inp['city']}"


def results_in_last_call(client):
    last = client.calls[-1]["messages"][-1]
    assert last["role"] == "user" and isinstance(last["content"], list), \
        f"the last message should be a user message with a list of tool_result blocks, got {last!r}"
    return last["content"]


def test_no_tool_use_returns_text_and_sends_tools():
    client = FakeAnthropic([reply(text("Hello!"))])
    got = run_tool_loop(client, "hi", [WEATHER], {"get_weather": weather})
    assert got == "Hello!", f"expected 'Hello!', got {got!r}"
    assert client.calls[0].get("tools") == [WEATHER], "send the tools list on every call"


def test_runs_tool_and_sends_result_back():
    call = tool_use("get_weather", {"city": "Lagos"}, id="toolu_a")
    client = FakeAnthropic([reply(call), reply(text("It's 31C in Lagos."))])
    got = run_tool_loop(client, "Weather in Lagos?", [WEATHER], {"get_weather": weather})
    assert got == "It's 31C in Lagos.", f"expected the final text, got {got!r}"
    msgs = client.calls[1]["messages"]
    assert msgs[1].get("role") == "assistant", "append the assistant turn (with its tool_use block) before the results"
    res = results_in_last_call(client)
    want = [{"type": "tool_result", "tool_use_id": "toolu_a", "content": "31C in Lagos"}]
    assert res == want, f"expected {want!r}, got {res!r}"


def test_all_results_for_one_turn_go_in_one_message():
    a = tool_use("get_weather", {"city": "Lagos"}, id="toolu_1")
    b = tool_use("get_weather", {"city": "Accra"}, id="toolu_2")
    client = FakeAnthropic([reply(text("Checking both."), a, b), reply(text("Done."))])
    run_tool_loop(client, "Lagos and Accra?", [WEATHER], {"get_weather": weather})
    msgs = client.calls[1]["messages"]
    assert len(msgs) == 3, f"expected 3 messages (user, assistant, user with 2 results), got {len(msgs)}"
    ids = [r.get("tool_use_id") for r in results_in_last_call(client)]
    assert ids == ["toolu_1", "toolu_2"], f"expected both results in one message, got ids {ids!r}"


def test_handler_error_is_reported_with_is_error():
    def broken(inp):
        raise TimeoutError("weather service down")

    client = FakeAnthropic([reply(tool_use("get_weather", {"city": "Lagos"})), reply(text("Sorry."))])
    got = run_tool_loop(client, "Weather?", [WEATHER], {"get_weather": broken})
    assert got == "Sorry.", "a failing tool must not crash the loop"
    res = results_in_last_call(client)[0]
    assert res.get("is_error") is True, f"set is_error True for a failing tool, got {res!r}"
    assert "weather service down" in str(res.get("content")), "put the error message in the tool_result content"


def test_unknown_tool_is_reported_with_is_error():
    client = FakeAnthropic([reply(tool_use("launch_rocket", {})), reply(text("Can't do that."))])
    run_tool_loop(client, "Go", [WEATHER], {"get_weather": weather})
    res = results_in_last_call(client)[0]
    assert res.get("is_error") is True, f"an unknown tool name should give is_error True, got {res!r}"


def test_stops_after_max_turns():
    script = [reply(tool_use("get_weather", {"city": "Lagos"})) for _ in range(3)]
    client = FakeAnthropic(script)
    try:
        run_tool_loop(client, "Weather?", [WEATHER], {"get_weather": weather}, max_turns=3)
    except RuntimeError:
        assert len(client.calls) == 3, f"expected exactly 3 calls, got {len(client.calls)}"
        return
    raise AssertionError("expected RuntimeError when Claude keeps asking for tools past max_turns")
