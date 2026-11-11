from solution import RateLimiter


def limiter_at(limit=2, window=60):
    now = [0.0]
    return RateLimiter(limit=limit, window=window, clock=lambda: now[0]), now


def test_allows_up_to_the_limit_then_blocks():
    limiter, _ = limiter_at(limit=3)
    got = [limiter.allow("ada") for _ in range(5)]
    assert got == [True, True, True, False, False], f"expected [True, True, True, False, False], got {got!r}"


def test_users_are_independent():
    limiter, _ = limiter_at(limit=1)
    assert limiter.allow("ada") is True, "ada's first request should be allowed"
    assert limiter.allow("ada") is False, "ada's second request should be blocked"
    assert limiter.allow("bayo") is True, "bayo has his own limit"


def test_old_requests_stop_counting_after_the_window():
    limiter, now = limiter_at(limit=2, window=60)
    limiter.allow("ada")            # t=0
    now[0] = 10.0
    limiter.allow("ada")            # t=10
    now[0] = 59.9
    assert limiter.allow("ada") is False, "at t=59.9 both requests still count"
    now[0] = 60.0
    assert limiter.allow("ada") is True, "at t=60 the request from t=0 no longer counts"
    assert limiter.allow("ada") is False, "t=10 and t=60 now fill the window"


def test_rejected_requests_do_not_count():
    limiter, now = limiter_at(limit=1, window=60)
    limiter.allow("ada")            # t=0
    for t in (20.0, 40.0, 59.0):
        now[0] = t
        limiter.allow("ada")        # all rejected
    now[0] = 60.0
    assert limiter.allow("ada") is True, "rejected requests must not extend the block"


def test_retry_after():
    limiter, now = limiter_at(limit=2, window=60)
    assert limiter.retry_after("ada") == 0.0, "a new user can go now"
    limiter.allow("ada")
    now[0] = 5.0
    limiter.allow("ada")
    got = limiter.retry_after("ada")
    assert abs(got - 55.0) < 1e-9, f"oldest request at 0, window 60, now 5: expected 55.0, got {got!r}"
    now[0] = 60.0
    assert limiter.retry_after("ada") == 0.0, "once the oldest request expires, retry_after is 0"
