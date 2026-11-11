from fake_llm import BadRequest, FakeAnthropic, Overloaded, RateLimited, reply, text
from solution import call_with_retry

REQ = {"model": "claude-opus-5-5", "max_tokens": 100, "messages": [{"role": "user", "content": "hi"}]}


def test_success_first_time_does_not_sleep():
    delays = []
    client = FakeAnthropic([reply(text("ok"))])
    resp = call_with_retry(client, REQ, sleep=delays.append)
    assert resp.content[0].text == "ok", "return the response from messages.create"
    assert delays == [], f"no sleeping when the first call works, got {delays!r}"
    assert client.calls[0] == REQ, f"pass the request through unchanged: expected {REQ!r}, got {client.calls[0]!r}"


def test_retries_rate_limit_then_succeeds():
    delays = []
    client = FakeAnthropic([RateLimited(), reply(text("ok"))])
    resp = call_with_retry(client, REQ, sleep=delays.append)
    assert resp.content[0].text == "ok", "after a 429, the retry's response should be returned"
    assert len(delays) == 1 and 1.0 <= delays[0] <= 2.0, f"first wait should be 1–2 s, got {delays!r}"


def test_backoff_grows_exponentially():
    delays = []
    client = FakeAnthropic([Overloaded(), Overloaded(), RateLimited(), reply(text("ok"))])
    call_with_retry(client, REQ, base_delay=0.5, sleep=delays.append)
    assert len(delays) == 3, f"expected 3 waits, got {delays!r}"
    for n, d in enumerate(delays):
        lo, hi = 0.5 * 2**n, 0.5 * 2**(n + 1)
        assert lo <= d <= hi, f"wait #{n} should be between {lo} and {hi} s, got {d}"


def test_bad_request_is_not_retried():
    delays = []
    client = FakeAnthropic([BadRequest(), reply(text("never reached"))])
    try:
        call_with_retry(client, REQ, sleep=delays.append)
    except BadRequest:
        assert len(client.calls) == 1 and delays == [], "a 400 must be raised immediately, with no retry or sleep"
        return
    raise AssertionError("expected the 400 error to be raised")


def test_gives_up_after_max_retries():
    delays = []
    client = FakeAnthropic([RateLimited() for _ in range(3)])
    try:
        call_with_retry(client, REQ, max_retries=2, sleep=delays.append)
    except RateLimited:
        assert len(client.calls) == 3, f"max_retries=2 means 3 calls in total, got {len(client.calls)}"
        assert len(delays) == 2, f"expected 2 waits (none after the last failure), got {len(delays)}"
        return
    raise AssertionError("expected the last RateLimited error to be raised")


def test_error_without_status_code_is_raised():
    class Boom(Exception):
        pass

    client = FakeAnthropic([Boom("bug in my code"), reply(text("never reached"))])
    try:
        call_with_retry(client, REQ, sleep=lambda s: None)
    except Boom:
        assert len(client.calls) == 1, "an error with no status_code should not be retried"
        return
    raise AssertionError("expected the exception to be re-raised")
