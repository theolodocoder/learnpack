import hashlib
import json
import time


def cache_key(model: str, system: str, messages: list[dict]) -> str:
    """Stable SHA-256 of everything that affects the answer."""
    payload = json.dumps({"model": model, "system": system, "messages": messages},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


class TTLCache:
    def __init__(self, ttl_seconds: float, clock=time.monotonic):
        self.ttl = ttl_seconds
        self.clock = clock
        self._data: dict[str, tuple[float, str]] = {}  # ponytail: unbounded in-memory dict; use Redis with EXPIRE in production

    def get(self, key: str) -> str | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self.clock() >= expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: str) -> None:
        self._data[key] = (self.clock() + self.ttl, value)


def cached_answer(client, cache: TTLCache, *, model: str, system: str, question: str,
                  max_tokens: int = 1024) -> str:
    messages = [{"role": "user", "content": question}]
    key = cache_key(model, system, messages)
    hit = cache.get(key)
    if hit is not None:
        return hit
    response = client.messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages)
    answer = "".join(b.text for b in response.content if b.type == "text")
    cache.set(key, answer)
    return answer


if __name__ == "__main__":
    import anthropic

    client = anthropic.Anthropic()
    cache = TTLCache(ttl_seconds=3600)
    for _ in range(2):
        t = time.perf_counter()
        a = cached_answer(client, cache, model="claude-haiku-5-5", system="Be brief.", question="What is a token bucket?")
        print(f"{time.perf_counter() - t:.2f}s", a[:80])
