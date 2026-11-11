import math
import time
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float, clock=time.monotonic):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.clock = clock
        # TODO: start full, and remember when you last refilled

    def allow(self, cost: float = 1.0) -> bool:
        # TODO: refill by (elapsed seconds x refill_per_sec), capped at capacity;
        #       if there are at least `cost` tokens, take them and return True
        return True

    def retry_after(self, cost: float = 1.0) -> float:
        # TODO: seconds until `cost` tokens are available (0.0 if they already are)
        return 0.0


def create_app(capacity: float, refill_per_sec: float, clock=time.monotonic) -> FastAPI:
    buckets: dict[str, TokenBucket] = {}

    def rate_limit(x_api_key: Annotated[str, Header()] = "anonymous") -> None:
        # TODO: one bucket per key; if it refuses, raise HTTPException(429, "Too many requests")
        #       with headers={"Retry-After": <whole seconds, rounded up, at least 1>}
        pass

    app = FastAPI()

    @app.get("/ask", dependencies=[Depends(rate_limit)])
    def ask() -> dict:
        return {"answer": "42"}

    return app


if __name__ == "__main__":
    now = [0.0]
    bucket = TokenBucket(capacity=3, refill_per_sec=1, clock=lambda: now[0])
    print([bucket.allow() for _ in range(4)])  # want [True, True, True, False]
    now[0] = 2.0
    print([bucket.allow() for _ in range(3)])  # want [True, True, False]
