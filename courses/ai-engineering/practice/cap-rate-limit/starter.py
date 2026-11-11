import time
from collections import deque


class RateLimiter:
    """At most `limit` requests per user in any `window` seconds."""

    def __init__(self, limit: int, window: float, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self.hits: dict[str, deque[float]] = {}

    def allow(self, user_id: str) -> bool:
        # TODO: drop times <= now - window, then allow and record if under the limit
        return True

    def retry_after(self, user_id: str) -> float:
        # TODO: 0.0 if allowed now, else oldest + window - now
        return 0.0


if __name__ == "__main__":
    now = [0.0]
    limiter = RateLimiter(limit=2, window=60, clock=lambda: now[0])
    print([limiter.allow("ada") for _ in range(3)])   # want [True, True, False]
    print(limiter.retry_after("ada"))                 # want 60.0
    now[0] = 60.0
    print(limiter.allow("ada"))                       # want True
