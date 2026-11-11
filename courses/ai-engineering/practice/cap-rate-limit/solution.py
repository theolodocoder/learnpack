import time
from collections import deque


class RateLimiter:
    """At most `limit` requests per user in any `window` seconds."""

    def __init__(self, limit: int, window: float, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self.hits: dict[str, deque[float]] = {}

    def _recent(self, user_id: str, now: float) -> deque[float]:
        times = self.hits.setdefault(user_id, deque())
        while times and times[0] <= now - self.window:
            times.popleft()
        return times

    def allow(self, user_id: str) -> bool:
        now = self.clock()
        times = self._recent(user_id, now)
        if len(times) < self.limit:
            times.append(now)
            return True
        return False

    def retry_after(self, user_id: str) -> float:
        now = self.clock()
        times = self._recent(user_id, now)
        if len(times) < self.limit:
            return 0.0
        return times[0] + self.window - now
