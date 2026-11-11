# Trim a conversation to fit the context window

The model only sees what you send, and everything you send must fit in its context window. Long chats eventually have to drop old turns.

Write two functions:

```python
def estimate_tokens(text: str) -> int: ...
def trim_history(messages: list[dict], budget: int) -> list[dict]: ...
```

1. `estimate_tokens` uses the rough rule of thumb **1 token ≈ 4 characters**, rounded **up**: `ceil(len(text) / 4)`. An empty string is 0 tokens.
2. `trim_history` keeps the **most recent** messages whose estimated tokens (of each message's `"content"` string) add up to **at most** `budget`. Walk backwards from the newest message and stop at the first one that doesn't fit.
3. The API requires the first message to be from the `user`, so after trimming, drop any `assistant` messages left at the front.
4. Return a new list in the original order. Don't modify the input list.

## Example

```python
msgs = [
    {"role": "user", "content": "a" * 40},       # 10 tokens
    {"role": "assistant", "content": "b" * 40},  # 10 tokens
    {"role": "user", "content": "c" * 20},       # 5 tokens
]
trim_history(msgs, 15)
# [{"role": "user", "content": "ccccc..."}]
# The newest two fit (15 tokens) but the result would start with "assistant", so that one is dropped too.
```
