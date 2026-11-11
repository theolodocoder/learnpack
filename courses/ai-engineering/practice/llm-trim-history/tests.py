from solution import estimate_tokens, trim_history


def msg(role, n_chars, ch="x"):
    return {"role": role, "content": ch * n_chars}


def test_estimate_tokens_rounds_up():
    for text, want in [("", 0), ("abcd", 1), ("abcde", 2), ("a" * 400, 100)]:
        got = estimate_tokens(text)
        assert got == want, f"estimate_tokens({text[:10]!r}...) : expected {want}, got {got}"


def test_keeps_everything_under_budget():
    msgs = [msg("user", 8), msg("assistant", 8), msg("user", 8)]
    got = trim_history(msgs, 100)
    assert got == msgs, f"expected all 3 messages kept, got {got!r}"


def test_drops_oldest_first():
    msgs = [msg("user", 40, "a"), msg("assistant", 40, "b"), msg("user", 40, "c"), msg("assistant", 40, "d"), msg("user", 40, "e")]
    got = trim_history(msgs, 30)
    want = msgs[2:]
    assert got == want, f"expected the newest 3 messages (30 tokens), got {[m['content'][0] for m in got]!r}"


def test_result_starts_with_user():
    msgs = [msg("user", 40, "a"), msg("assistant", 40, "b"), msg("user", 20, "c")]
    got = trim_history(msgs, 15)
    assert got == [msgs[2]], f"a leading assistant message must be dropped; got {got!r}"


def test_does_not_modify_input():
    msgs = [msg("user", 40), msg("assistant", 40), msg("user", 40)]
    before = list(msgs)
    trim_history(msgs, 10)
    assert msgs == before, "trim_history changed the list it was given; return a new list instead"


def test_newest_message_too_big_returns_empty():
    msgs = [msg("user", 4), msg("assistant", 4), msg("user", 400)]
    got = trim_history(msgs, 50)
    assert got == [], f"the newest message alone is over budget, so nothing fits; got {got!r}"
