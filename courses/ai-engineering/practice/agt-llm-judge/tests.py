import json

from fake_llm import FakeAnthropic, reply, text
from solution import Verdict, llm_judge, pairwise


def verdict(score, passed):
    return reply(text(json.dumps({"reasoning": "Clear steps.", "score": score, "passed": passed})))


def pref(winner):
    return reply(text(json.dumps({"reasoning": "...", "winner": winner})))


def sent(call):
    return str(call["messages"][-1]["content"])


def test_judge_returns_parsed_verdict():
    client = FakeAnthropic([verdict(5, True)])
    got = llm_judge(client, "How do I reset my password?", "Click 'Forgot password'.", "Must give steps.")
    assert isinstance(got, Verdict), f"return response.parsed_output (a Verdict), got {type(got).__name__}"
    assert (got.score, got.passed) == (5, True), f"got {got!r}"
    assert client.calls[0].get("output_format") is Verdict, "pass output_format=Verdict to messages.parse"


def test_judge_wraps_inputs_in_tags():
    client = FakeAnthropic([verdict(2, False)])
    llm_judge(client, "Q?", "The answer", "The rubric")
    msg = sent(client.calls[0])
    for tag, value in (("question", "Q?"), ("answer", "The answer"), ("rubric", "The rubric")):
        assert f"<{tag}>" in msg and f"</{tag}>" in msg and value in msg, f"put the {tag} inside <{tag}> tags"
    assert client.calls[0].get("system"), "give the judge a system prompt"


def test_score_must_be_between_1_and_5():
    for bad in (0, 6):
        try:
            Verdict(reasoning="x", score=bad, passed=True)
        except ValueError:
            continue
        raise AssertionError(f"Verdict should reject score={bad}: use Field(ge=1, le=5)")


def test_pairwise_swaps_order_and_agrees():
    client = FakeAnthropic([pref("first"), pref("second")])
    got = pairwise(client, "Explain recursion", "ANSWER_A", "ANSWER_B")
    assert got == "A", f"A won in both orders, expected 'A', got {got!r}"
    one, two = sent(client.calls[0]), sent(client.calls[1])
    assert one.index("ANSWER_A") < one.index("ANSWER_B"), "call 1 should show answer A first"
    assert two.index("ANSWER_B") < two.index("ANSWER_A"), "call 2 should show answer B first"
    assert "<first>" in one and "<second>" in one, "wrap the answers in <first> and <second> tags"


def test_pairwise_disagreement_is_a_tie():
    client = FakeAnthropic([pref("first"), pref("first")])  # always prefers whatever comes first
    got = pairwise(client, "Q", "a", "b")
    assert got == "tie", f"a judge that just picks position 1 should give 'tie', got {got!r}"
    client = FakeAnthropic([pref("second"), pref("first")])
    assert pairwise(client, "Q", "a", "b") == "B", "B won in both orders"
