import json
from collections.abc import Iterable, Iterator


def parse_events(lines: Iterable[str]) -> Iterator[dict]:
    """Yield one dict per valid JSON line, skipping blanks and junk."""
    # TODO: loop over lines, strip, skip blanks, try json.loads, skip errors
    #       and non-dicts, yield the dict
    yield from ()


def collect_text(events: Iterable[dict]) -> str:
    """Join the text of every text_delta event."""
    # TODO
    return ""


if __name__ == "__main__":
    lines = [
        '{"type": "message_start"}',
        '{"type": "text_delta", "text": "Hel"}',
        "",
        "garbage",
        '{"type": "text_delta", "text": "lo!"}',
        '{"type": "message_stop"}',
    ]
    print(repr(collect_text(parse_events(lines))))
