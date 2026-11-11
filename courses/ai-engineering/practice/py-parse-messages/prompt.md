# Parse a chat history

Chat APIs take a list of messages, each with a `role` and some `content`. Data you load from a file or a request is often messy, so you'll clean it into a typed dataclass first.

Write a dataclass and two functions:

```python
@dataclass
class Message:
    role: str
    content: str

def parse_messages(raw: list[dict]) -> list[Message]:
def transcript(messages: list[Message]) -> str:
```

**`parse_messages`** turns a list of dicts into `Message` objects, keeping the order. Skip (don't crash on) any item that:

- is missing `"role"` or `"content"`, or
- has a role other than `"user"` or `"assistant"`, or
- has content that is empty or only whitespace.

Strip surrounding whitespace from the content you keep.

**`transcript`** returns one line per message, formatted `role: content`, joined with `"\n"`. An empty list gives `""`.

Example:

```python
raw = [
    {"role": "user", "content": "  Hi! "},
    {"role": "system", "content": "ignored"},
    {"content": "no role"},
    {"role": "assistant", "content": "Hello."},
]
msgs = parse_messages(raw)
# [Message(role='user', content='Hi!'), Message(role='assistant', content='Hello.')]
print(transcript(msgs))
# user: Hi!
# assistant: Hello.
```

Tip: a list comprehension with a helper check, or a plain loop with `continue`, both work.
