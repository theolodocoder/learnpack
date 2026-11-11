import types

from solution import collect_text, parse_events

LINES = [
    '{"type": "message_start"}',
    '{"type": "text_delta", "text": "Hel"}',
    "",
    "garbage",
    '{"type": "text_delta", "text": "lo!"}',
    '{"type": "message_stop"}',
]


def test_parse_events_is_a_generator():
    got = parse_events(LINES)
    assert isinstance(got, types.GeneratorType), f"parse_events should return a generator, got {type(got).__name__}"


def test_parse_events_skips_blank_and_invalid_lines():
    got = list(parse_events(LINES + ["  ", "[1, 2]", "{broken"]))
    types_seen = [e["type"] for e in got]
    want = ["message_start", "text_delta", "text_delta", "message_stop"]
    assert types_seen == want, f"expected event types {want!r}, got {types_seen!r}"


def test_parse_events_yields_before_reading_everything():
    def lines():
        yield '{"type": "text_delta", "text": "first"}'
        raise AssertionError("parse_events read past the first line before yielding it; it should be lazy")

    first = next(parse_events(lines()))
    assert first == {"type": "text_delta", "text": "first"}, f"got {first!r}"


def test_collect_text_joins_text_deltas_in_order():
    got = collect_text(parse_events(LINES))
    assert got == "Hello!", f"expected 'Hello!', got {got!r}"


def test_collect_text_of_no_text_is_empty():
    got = collect_text([{"type": "message_start"}, {"type": "message_stop"}])
    assert got == "", f"expected '', got {got!r}"
