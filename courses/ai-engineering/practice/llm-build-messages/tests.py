from solution import build_messages


def test_empty_history_gives_one_user_message():
    got = build_messages([], "Hello")
    want = [{"role": "user", "content": "Hello"}]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_pairs_become_alternating_roles():
    got = build_messages([("Hi", "Hello!"), ("Name?", "Claude.")], "Bye")
    want = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "Name?"},
        {"role": "assistant", "content": "Claude."},
        {"role": "user", "content": "Bye"},
    ]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_first_and_last_messages_are_user():
    got = build_messages([("a", "b"), ("c", "d"), ("e", "f")], "g")
    assert got[0]["role"] == "user" and got[-1]["role"] == "user", "the list must start and end with a user message"
    assert len(got) == 7, f"3 pairs + 1 new message should give 7 messages, got {len(got)}"


def test_blank_message_raises_value_error():
    for bad in ["", "   ", "\n"]:
        try:
            build_messages([], bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for new_message={bad!r}")
