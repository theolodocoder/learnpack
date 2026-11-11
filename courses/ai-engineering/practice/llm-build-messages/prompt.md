# Build the messages list for a multi-turn chat

The Messages API is stateless: every call must include the whole conversation so far. Your app usually stores the chat in its own format, so you need to convert it.

Write:

```python
def build_messages(history: list[tuple[str, str]], new_message: str) -> list[dict]: ...
```

- `history` is a list of finished turns, each a `(user_text, assistant_text)` pair, oldest first.
- Return the list the API expects: alternating `{"role": "user", "content": ...}` and `{"role": "assistant", "content": ...}` dicts for each pair, followed by the new user message.
- If `new_message` is empty or only whitespace, raise `ValueError` (the API rejects empty content, so catch it early).

## Example

```python
build_messages([("Hi", "Hello! How can I help?")], "What's 2 + 2?")
# [
#   {"role": "user", "content": "Hi"},
#   {"role": "assistant", "content": "Hello! How can I help?"},
#   {"role": "user", "content": "What's 2 + 2?"},
# ]
```
