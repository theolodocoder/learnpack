# One turn of a chat with Claude

Write the function at the heart of every chatbot:

```python
def chat_once(client, system: str, history: list[dict], user_msg: str,
              model: str = "claude-opus-5-5") -> tuple[str, list[dict]]: ...
```

1. Call `client.messages.create(...)` with `model`, a `max_tokens` (use `16000`), the `system` prompt, and `messages` = the whole `history` **plus** the new user message `{"role": "user", "content": user_msg}`.
2. Join the text of every `text` block in `response.content` into one string (skip any block whose `.type` isn't `"text"`).
3. Return `(reply_text, new_history)`, where `new_history` is the old history plus the user message plus `{"role": "assistant", "content": reply_text}`.
4. Don't modify the `history` list you were given; build a new one.

## Example

```python
reply, history = chat_once(client, "You are terse.", [], "Capital of Nigeria?")
# reply   == "Abuja."
# history == [{"role": "user", "content": "Capital of Nigeria?"},
#             {"role": "assistant", "content": "Abuja."}]
reply, history = chat_once(client, "You are terse.", history, "Population?")
# the second call sends all 3 messages
```

**Check is free and offline:** the tests pass in a fake client that records what you sent. **Run** uses the real API if your `ANTHROPIC_API_KEY` is set.
