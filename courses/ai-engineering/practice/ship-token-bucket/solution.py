import math
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float, clock=time.monotonic):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.clock = clock
        self.tokens = float(capacity)  # start full, so a new client can burst
        self.updated = clock()

    def _refill(self) -> None:
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.refill_per_sec)
        self.updated = now

    def allow(self, cost: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def retry_after(self, cost: float = 1.0) -> float:
        """Seconds until `cost` tokens will be available (0 if they already are)."""
        self._refill()
        return max(0.0, (cost - self.tokens) / self.refill_per_sec)


def create_app(capacity: float, refill_per_sec: float, clock=time.monotonic) -> FastAPI:
    buckets: dict[str, TokenBucket] = {}  # ponytail: in-process dict; use Redis once you run more than one instance

    def rate_limit(x_api_key: Annotated[str, Header()] = "anonymous") -> None:
        bucket = buckets.setdefault(x_api_key, TokenBucket(capacity, refill_per_sec, clock))
        if not bucket.allow():
            wait = math.ceil(bucket.retry_after())
            raise HTTPException(429, "Too many requests", headers={"Retry-After": str(max(1, wait))})

    app = FastAPI()

    @app.get("/ask", dependencies=[Depends(rate_limit)])
    def ask() -> dict:
        return {"answer": "42"}

    return app


if __name__ == "__main__":
    now = [0.0]
    bucket = TokenBucket(capacity=3, refill_per_sec=1, clock=lambda: now[0])
    print([bucket.allow() for _ in range(4)])  # [True, True, True, False]
    now[0] = 2.0
    print([bucket.allow() for _ in range(3)])  # [True, True, False]
