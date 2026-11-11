# Rate limiting with a token bucket

Every call to your API costs you money at Anthropic, so one client mustn't be able to fire 10,000 requests a minute. Implement a token bucket and use it in a FastAPI dependency.

```python
class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float, clock=time.monotonic): ...
    def allow(self, cost: float = 1.0) -> bool: ...
    def retry_after(self, cost: float = 1.0) -> float: ...

def create_app(capacity: float, refill_per_sec: float, clock=time.monotonic) -> FastAPI: ...
```

**The bucket:**

- It starts **full** (`capacity` tokens).
- Before every check, add `(now − last_time) × refill_per_sec` tokens, but never more than `capacity`. Then set `last_time = now`. Get `now` from `self.clock()`, never from `time` directly, so tests control time without sleeping.
- `allow(cost)`: if there are at least `cost` tokens, subtract them and return `True`; otherwise return `False` and take nothing.
- `retry_after(cost)`: seconds until `cost` tokens will be there: `max(0, (cost − tokens) / refill_per_sec)`.

**The app:** a dependency `rate_limit` keeps one bucket per `X-API-Key` header value (`"anonymous"` if missing). When the bucket refuses, raise `HTTPException(429, "Too many requests", headers={"Retry-After": ...})`, where `Retry-After` is the whole number of seconds from `retry_after()`, rounded **up** (`math.ceil`), and at least `1`. `GET /ask` uses it.

## Example

```python
now = [0.0]
b = TokenBucket(capacity=3, refill_per_sec=1, clock=lambda: now[0])
[b.allow() for _ in range(4)]   # [True, True, True, False]
now[0] = 2.0                    # two seconds later: 2 tokens back
[b.allow() for _ in range(3)]   # [True, True, False]
```
