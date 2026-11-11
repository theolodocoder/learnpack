import hashlib
import json
import time


def cache_key(model: str, system: str, messages: list[dict]) -> str:
    """SHA-256 hex digest of model + system + messages, independent of dict key order."""
    # TODO: json.dumps(..., sort_keys=True, separators=(",", ":")) then hashlib.sha256
    return ""


class TTLCache:
    def __init__(self, ttl_seconds: float, clock=time.monotonic):
        self.ttl = ttl_seconds
        self.clock = clock
        self._data: dict[str, tuple[float, str]] = {}  # key -> (expires_at, value)

    def get(self, key: str) -> str | None:
        # TODO: None if missing or expired (now >= expires_at; delete expired entries)
        return None

    def set(self, key: str, value: str) -> None:
        # TODO: store with expires_at = now + ttl
        pass


def cached_answer(client, cache: TTLCache, *, model: str, system: str, question: str,
                  max_tokens: int = 1024) -> str:
    messages = [{"role": "user", "content": question}]
    # TODO: return the cached answer if there is one
    response = client.messages.create(model=model, max_tokens=max_tokens, system=system, messages=messages)
    answer = "".join(b.text for b in response.content if b.type == "text")
    # TODO: store the answer before returning it
    return answer


if __name__ == "__main__":
    import anthropic

    client = anthropic.Anthropic()
    cache = TTLCache(ttl_seconds=3600)
    try:
        for _ in range(2):
            t = time.perf_counter()
            a = cached_answer(client, cache, model="claude-haiku-5-5", system="Be brief.", question="What is a token bucket?")
            print(f"{time.perf_counter() - t:.2f}s", a[:80])
    except Exception as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", type(e).__name__)
