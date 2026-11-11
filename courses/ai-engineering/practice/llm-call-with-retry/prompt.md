# Retry with exponential backoff and jitter

Write:

```python
def call_with_retry(client, request: dict, max_retries: int = 3,
                    base_delay: float = 1.0, sleep=time.sleep): ...
```

It calls `client.messages.create(**request)` and returns the response, retrying failures that are worth retrying.

1. **Retryable:** an exception whose `status_code` is `429` (rate limited) or `>= 500` (server error, including `529` overloaded).
2. **Not retryable:** any other status code (e.g. `400` bad request, `401` bad key). Re-raise immediately, with no sleep. An exception with no `status_code` attribute at all is also re-raised immediately. Use `getattr(e, "status_code", None)`.
3. Make at most `1 + max_retries` calls. If the last one still fails, re-raise its exception.
4. Before retry number `n` (counting from 0), wait `base_delay · 2ⁿ` seconds **plus** random jitter `random.uniform(0, base_delay · 2ⁿ)`. So the first wait is between 1 and 2 s, the second between 2 and 4 s, the third between 4 and 8 s (with `base_delay=1`).
5. Wait by calling the `sleep` argument, not `time.sleep` directly. Tests pass a fake `sleep` that records the delays instead of waiting.

## Example

```python
delays = []
resp = call_with_retry(client, {"model": "claude-opus-5-5", "max_tokens": 1000, "messages": [...]},
                       sleep=delays.append)
# if the first call got a 429 and the second worked:
# delays == [1.37]   (somewhere between 1 and 2)
```

**Check is free and offline:** the fake client raises scripted errors with `.status_code` 429, 529 or 400. **Run** uses the real API if your key is set.
