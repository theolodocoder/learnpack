from fake_llm import FakeAnthropic, reply, text
from solution import classify_sentiment, evaluate


def test_extracts_label_from_tags():
    client = FakeAnthropic([reply(text("Sure. <label> Positive </label> Hope that helps."))])
    got = classify_sentiment(client, "Love it")
    assert got == "positive", f"expected 'positive', got {got!r}"


def test_review_is_wrapped_in_tags():
    client = FakeAnthropic([reply(text("<label>negative</label>"))])
    classify_sentiment(client, "Broke after a day")
    msgs = client.calls[0].get("messages") or []
    assert len(msgs) == 1 and msgs[0].get("role") == "user", f"send exactly one user message, got {msgs!r}"
    content = msgs[0].get("content")
    assert isinstance(content, str) and "<review>\nBroke after a day\n</review>" in content, \
        f"expected the review inside <review>\\n...\\n</review>, got {content!r}"


def test_system_prompt_names_all_labels():
    client = FakeAnthropic([reply(text("<label>neutral</label>"))])
    classify_sentiment(client, "It is a cable.")
    system = client.calls[0].get("system") or ""
    for label in ("positive", "negative", "neutral", "<label>"):
        assert label in system, f"your system prompt should mention {label!r}"


def test_unknown_when_missing_or_invalid():
    client = FakeAnthropic([reply(text("I think it's positive")), reply(text("<label>angry</label>"))])
    a = classify_sentiment(client, "x")
    b = classify_sentiment(client, "y")
    assert a == "unknown", f"no <label> tags should give 'unknown', got {a!r}"
    assert b == "unknown", f"a label outside LABELS should give 'unknown', got {b!r}"


def test_evaluate_returns_accuracy():
    client = FakeAnthropic([
        reply(text("<label>positive</label>")),
        reply(text("<label>positive</label>")),
        reply(text("<label>neutral</label>")),
    ])
    cases = [("Great!", "positive"), ("Awful.", "negative"), ("A phone.", "neutral")]
    got = evaluate(client, cases)
    assert abs(got - 2 / 3) < 1e-9, f"2 of 3 correct should give 0.666..., got {got!r}"
    assert len(client.calls) == 3, f"expected one API call per case (3), got {len(client.calls)}"


def test_evaluate_empty_is_zero():
    got = evaluate(FakeAnthropic(), [])
    assert got == 0.0, f"expected 0.0 for no cases, got {got!r}"
