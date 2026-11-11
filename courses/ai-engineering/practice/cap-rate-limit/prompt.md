# Rate-limit the public

The moment your product is public, someone will send it 500 messages in a minute: a curious user, a script, or a WhatsApp group forwarding the link. Each one costs you tokens. A per-user rate limit caps the damage.

Write a sliding-window rate limiter:

```python
class RateLimiter:
    def __init__(self, limit: int, window: float, clock=time.monotonic): ...
    def allow(self, user_id: str) -> bool: ...
    def retry_after(self, user_id: str) -> float: ...
```

- Each user may make at most `limit` requests in any `window` seconds.
- `allow(user_id)`:
  - forget that user's request times that are `window` or more seconds old (a request at time `t` stops counting at `t + window`);
  - if fewer than `limit` remain, record the current time and return `True`;
  - otherwise return `False` and record nothing (rejected requests don't count).
- `retry_after(user_id)` returns how many seconds until `allow` would next succeed for that user: `0.0` if it would succeed now, otherwise `oldest_counted_request + window - now`.
- Users are independent.
- `clock` is a function returning the current time in seconds. Tests pass a fake clock so nothing sleeps. Always call `self.clock()`, never `time.monotonic()` directly.

Use a `dict` of `collections.deque`s: append new times on the right, drop old ones from the left.

## Example

```python
now = [0.0]
limiter = RateLimiter(limit=2, window=60, clock=lambda: now[0])
limiter.allow("ada"), limiter.allow("ada"), limiter.allow("ada")   # (True, True, False)
limiter.retry_after("ada")   # 60.0
now[0] = 30.0
limiter.retry_after("ada")   # 30.0
limiter.allow("bayo")        # True: users are independent
now[0] = 60.0
limiter.allow("ada")         # True: the request at 0.0 no longer counts
```
