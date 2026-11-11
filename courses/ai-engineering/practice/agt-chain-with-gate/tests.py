from fake_llm import FakeAnthropic, reply, text
from solution import outline_then_draft

GOOD = "- Bugs are expensive\n- Tests document intent\n- Refactor without fear"


def user_content(call):
    content = call["messages"][-1]["content"]
    return content if isinstance(content, str) else str(content)


def test_returns_outline_and_draft():
    client = FakeAnthropic([reply(text(GOOD)), reply(text("Tests matter because..."))])
    got = outline_then_draft(client, "Why tests matter")
    want = {"outline": GOOD, "draft": "Tests matter because..."}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_topic_is_wrapped_in_tags():
    client = FakeAnthropic([reply(text(GOOD)), reply(text("Draft"))])
    outline_then_draft(client, "Why tests matter")
    first = user_content(client.calls[0])
    assert "<topic>Why tests matter</topic>" in first, f"put the topic in <topic> tags, got {first!r}"


def test_second_call_contains_outline_in_tags():
    client = FakeAnthropic([reply(text(GOOD)), reply(text("Draft"))])
    outline_then_draft(client, "Why tests matter")
    assert len(client.calls) == 2, f"expected 2 calls, got {len(client.calls)}"
    second = user_content(client.calls[1])
    assert "<outline>" in second and "</outline>" in second, "wrap the outline in <outline> tags in call 2"
    assert "Refactor without fear" in second, "send the outline text itself in call 2"


def test_gate_stops_before_second_call():
    client = FakeAnthropic([reply(text("- Only one point\nand some prose")), reply(text("Draft"))])
    try:
        outline_then_draft(client, "Thin topic")
    except ValueError:
        assert len(client.calls) == 1, f"the gate must stop before call 2, but {len(client.calls)} calls were made"
        return
    raise AssertionError("expected ValueError for an outline with fewer than 3 bullet points")


def test_indented_bullets_count():
    outline = "Outline:\n  - one\n  - two\n  - three"
    client = FakeAnthropic([reply(text(outline)), reply(text("Draft"))])
    got = outline_then_draft(client, "Topic")
    assert got["draft"] == "Draft", "indented '- ' lines should count as bullet points"
