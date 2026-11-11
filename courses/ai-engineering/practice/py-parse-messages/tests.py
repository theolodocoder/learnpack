from solution import Message, parse_messages, transcript


def test_parses_valid_messages_in_order():
    got = parse_messages([{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}])
    want = [Message("user", "Hi"), Message("assistant", "Hello")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_strips_whitespace_from_content():
    got = parse_messages([{"role": "user", "content": "  padded \n"}])
    want = [Message("user", "padded")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_skips_bad_items_without_crashing():
    raw = [
        {"role": "system", "content": "wrong role"},
        {"content": "no role"},
        {"role": "user"},
        {"role": "user", "content": "   "},
        {"role": "assistant", "content": "kept"},
    ]
    got = parse_messages(raw)
    want = [Message("assistant", "kept")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_transcript_formats_one_line_per_message():
    got = transcript([Message("user", "Hi!"), Message("assistant", "Hello.")])
    want = "user: Hi!\nassistant: Hello."
    assert got == want, f"expected {want!r}, got {got!r}"


def test_transcript_of_empty_list_is_empty_string():
    got = transcript([])
    assert got == "", f"expected '', got {got!r}"
