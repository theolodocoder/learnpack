# A streaming pipeline

LLM APIs stream their answer as a sequence of small events, one per line. Some are text pieces, some are bookkeeping. Build a lazy pipeline that turns raw lines into the final text.

Write two functions:

```python
def parse_events(lines: Iterable[str]) -> Iterator[dict]:
def collect_text(events: Iterable[dict]) -> str:
```

**`parse_events`** is a generator:

- Strip each line. Skip blank lines.
- Parse the rest with `json.loads`. Skip lines that aren't valid JSON, or that parse to something other than a dict.
- Yield each dict as soon as it is parsed (don't build a list first).

**`collect_text`** joins the `"text"` field of every event whose `"type"` is `"text_delta"`, in order. Other events are ignored.

Example:

```python
lines = [
    '{"type": "message_start"}',
    '{"type": "text_delta", "text": "Hel"}',
    "",
    "garbage",
    '{"type": "text_delta", "text": "lo!"}',
    '{"type": "message_stop"}',
]
collect_text(parse_events(lines))   # 'Hello!'
```

Because both steps are lazy, this also works when `lines` is a file object or a network stream that is still arriving.
