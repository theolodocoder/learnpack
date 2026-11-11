# Cache repeated LLM answers with a TTL

Many apps get the same question again and again ("What are your opening hours?"). Answering from a cache is instant and free. Build one.

```python
def cache_key(model: str, system: str, messages: list[dict]) -> str: ...

class TTLCache:
    def __init__(self, ttl_seconds: float, clock=time.monotonic): ...
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...

def cached_answer(client, cache: TTLCache, *, model: str, system: str, question: str,
                  max_tokens: int = 1024) -> str: ...
```

1. **`cache_key`**: everything that changes the answer goes into the key. JSON-encode `{"model", "system", "messages"}` with `sort_keys=True` and `separators=(",", ":")`, so dict key order doesn't matter. Return the SHA-256 hex digest. A different model, system prompt or message must give a different key.
2. **`TTLCache`**: `set` stores `(now + ttl, value)`; `get` returns the value, or `None` if the key is missing or `now >= expires_at` (delete expired entries). Use `self.clock()` for `now`.
3. **`cached_answer`**: build `messages = [{"role": "user", "content": question}]`. On a cache hit, return the stored text **without calling the model**. On a miss, call `client.messages.create(model=..., max_tokens=..., system=..., messages=...)`, join the text blocks, store the result, and return it. If the call raises, let the error propagate and cache nothing.

## Example

```python
cache = TTLCache(ttl_seconds=3600)
cached_answer(client, cache, model="claude-haiku-5-5", system="Be brief.", question="What is RAG?")  # calls Claude
cached_answer(client, cache, model="claude-haiku-5-5", system="Be brief.", question="What is RAG?")  # instant, no call
```

Check is free and offline: the tests use a fake client and count its calls. Run with an API key set calls Haiku once and prints the time for the miss and the hit.
