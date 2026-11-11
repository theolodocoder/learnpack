# Wrap a stream in a generator

In a web app you rarely print chunks: you pass them on to something else (a FastAPI `StreamingResponse`, a WebSocket, a UI). A generator is the natural shape for that.

Write a **generator function**:

```python
def stream_text(client, prompt: str, system: str = "", model: str = "claude-opus-5-5"): ...
```

1. It opens `client.messages.stream(...)` with `model`, `max_tokens=64000`, `messages=[{"role": "user", "content": prompt}]`, and `system` **only if it's non-empty** (don't send `system=""`).
2. It `yield`s each chunk from `stream.text_stream`.
3. Because it's a generator, nothing happens until someone iterates it: calling `stream_text(...)` must **not** call the API yet.

## Example

```python
gen = stream_text(client, "Count to three")   # no API call yet
for chunk in gen:                              # the call happens here
    print(chunk, end="")
# One, two, three.
```

**Check is free and offline.** **Run** uses the real API if your key is set.
