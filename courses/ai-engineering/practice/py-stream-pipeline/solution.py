import json
from collections.abc import Iterable, Iterator


def parse_events(lines: Iterable[str]) -> Iterator[dict]:
    """Yield one dict per valid JSON line, skipping blanks and junk."""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def collect_text(events: Iterable[dict]) -> str:
    """Join the text of every text_delta event."""
    return "".join(e.get("text", "") for e in events if e.get("type") == "text_delta")


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
