from fastapi.testclient import TestClient

from solution import TokenBucket, create_app


class Clock:
    """A clock you move by hand: clock.now = 5.0"""
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_allows_a_burst_up_to_capacity_then_denies():
    clock = Clock()
    b = TokenBucket(capacity=3, refill_per_sec=1, clock=clock)
    got = [b.allow() for _ in range(4)]
    assert got == [True, True, True, False], f"expected [True, True, True, False], got {got}"


def test_refills_over_time():
    clock = Clock()
    b = TokenBucket(capacity=3, refill_per_sec=2, clock=clock)
    for _ in range(3):
        b.allow()
    clock.now = 0.5  # 0.5 s x 2 tokens/s = 1 token
    got = [b.allow(), b.allow()]
    assert got == [True, False], f"after 0.5 s at 2/s exactly one request should pass, got {got}"


def test_never_exceeds_capacity_after_idle():
    clock = Clock()
    b = TokenBucket(capacity=2, refill_per_sec=1, clock=clock)
    clock.now = 1000.0
    got = [b.allow() for _ in range(3)]
    assert got == [True, True, False], f"a long idle period must not store more than capacity, got {got}"


def test_retry_after_and_cost():
    clock = Clock()
    b = TokenBucket(capacity=4, refill_per_sec=0.5, clock=clock)
    assert b.allow(cost=4) is True, "a request costing the whole bucket should pass when full"
    assert b.allow(cost=1) is False, "the bucket is empty now"
    got = b.retry_after()
    assert abs(got - 2.0) < 1e-9, f"1 token at 0.5/s takes 2 s, got {got!r}"


def test_app_returns_429_with_retry_after_per_key():
    clock = Clock()
    client = TestClient(create_app(capacity=2, refill_per_sec=0.25, clock=clock))
    alice = {"X-API-Key": "alice"}
    codes = [client.get("/ask", headers=alice).status_code for _ in range(3)]
    assert codes == [200, 200, 429], f"expected [200, 200, 429] for alice, got {codes}"
    r = client.get("/ask", headers=alice)
    assert r.headers.get("retry-after") == "4", f"1 token at 0.25/s needs 4 s: expected Retry-After '4', got {r.headers.get('retry-after')!r}"
    bob = client.get("/ask", headers={"X-API-Key": "bob"})
    assert bob.status_code == 200, f"each key has its own bucket: bob should get 200, got {bob.status_code}"
    clock.now = 4.0
    again = client.get("/ask", headers=alice)
    assert again.status_code == 200, f"after waiting 4 s alice should get through, got {again.status_code}"
