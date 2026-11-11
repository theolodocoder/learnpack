import copy

from fake_llm import FakeAnthropic, reply, text
from solution import compact_history


def u(t): return {"role": "user", "content": t}
def a(t): return {"role": "assistant", "content": t}


HISTORY = [u("My name is Ada"), a("Hi Ada"), u("I use Postgres 16"), a("Noted"),
           u("Why is my query slow?"), a("Can you share it?"), u("SELECT 1")]


def test_short_history_is_unchanged_and_free():
    client = FakeAnthropic([])
    msgs = [u("hi"), a("hello")]
    got = compact_history(client, msgs, keep_last=4)
    assert got == msgs, f"expected the history unchanged, got {got!r}"
    assert got is not msgs, "return a copy, not the same list"
    assert client.calls == [], "don't call the API when there's nothing to summarise"


def test_keeps_recent_turns_with_summary_in_front():
    client = FakeAnthropic([reply(text("User is Ada, uses Postgres 16."))])
    got = compact_history(client, HISTORY, keep_last=3)
    want = [u("<summary>\nUser is Ada, uses Postgres 16.\n</summary>\n\nWhy is my query slow?"),
            a("Can you share it?"), u("SELECT 1")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_summary_call_sees_old_turns_only():
    client = FakeAnthropic([reply(text("summary"))])
    compact_history(client, HISTORY, keep_last=3, model="claude-haiku-5-5")
    call = client.calls[0]
    assert call.get("model") == "claude-haiku-5-5", f"summarise with `model`, got {call.get('model')!r}"
    sent = str(call["messages"][-1]["content"])
    assert "<transcript>" in sent and "user: My name is Ada" in sent and "assistant: Noted" in sent, \
        f"send old turns as 'role: content' lines inside <transcript> tags, got {sent!r}"
    assert "SELECT 1" not in sent, "don't summarise the turns you keep"


def test_boundary_moves_back_so_first_kept_message_is_user():
    client = FakeAnthropic([reply(text("S"))])
    got = compact_history(client, HISTORY, keep_last=2)  # last 2 would start with "Can you share it?"
    assert got[0]["role"] == "user", f"the first kept message must be a user message, got {got[0]!r}"
    assert len(got) == 3 and got[0]["content"].endswith("Why is my query slow?"), \
        f"keep one more message so the history starts with the user, got {got!r}"


def test_input_is_not_modified():
    client = FakeAnthropic([reply(text("S"))])
    before = copy.deepcopy(HISTORY)
    compact_history(client, HISTORY, keep_last=3)
    assert HISTORY == before, "compact_history must not modify the messages it was given"
