from solution import retry


def _flaky(failures: int, exc: BaseException):
    """A function that raises `exc` for its first `failures` calls, then returns 'ok'."""
    state = {"calls": 0}

    def f():
        state["calls"] += 1
        if state["calls"] <= failures:
            raise exc
        return "ok"

    return f, state


def test_returns_after_transient_failures_with_doubling_delays():
    delays = []
    f, state = _flaky(2, ConnectionError("blip"))
    wrapped = retry(times=3, base_delay=0.1, sleep=delays.append)(f)
    got = wrapped()
    assert got == "ok", f"expected 'ok', got {got!r}"
    assert state["calls"] == 3, f"expected 3 calls, got {state['calls']}"
    assert delays == [0.1, 0.2], f"expected delays [0.1, 0.2], got {delays!r}"


def test_no_sleep_when_first_call_succeeds():
    delays = []
    f, state = _flaky(0, ConnectionError())
    assert retry(sleep=delays.append)(f)() == "ok"
    assert delays == [] and state["calls"] == 1, f"expected 1 call and no sleeps, got calls={state['calls']} delays={delays!r}"


def test_reraises_last_error_after_all_attempts():
    delays = []
    f, state = _flaky(10, TimeoutError("still down"))
    wrapped = retry(times=4, base_delay=1, sleep=delays.append)(f)
    try:
        wrapped()
    except TimeoutError as e:
        assert str(e) == "still down", f"expected the original error, got {e!r}"
    else:
        raise AssertionError("expected TimeoutError after all attempts failed")
    assert state["calls"] == 4, f"expected 4 calls, got {state['calls']}"
    assert delays == [1, 2, 4], f"expected delays [1, 2, 4] (no sleep after the last try), got {delays!r}"


def test_does_not_retry_other_exceptions():
    delays = []
    f, state = _flaky(5, ValueError("bad input"))
    wrapped = retry(times=3, retry_on=(ConnectionError,), sleep=delays.append)(f)
    try:
        wrapped()
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError to be raised straight away")
    assert state["calls"] == 1 and delays == [], f"ValueError is not in retry_on, so no retries: calls={state['calls']}"


def test_keeps_function_name_and_docstring():
    @retry(sleep=lambda s: None)
    def ask_model():
        """Ask the model something."""
        return 42

    assert ask_model.__name__ == "ask_model", f"__name__ is {ask_model.__name__!r}; did you use functools.wraps?"
    assert ask_model.__doc__ == "Ask the model something.", f"__doc__ is {ask_model.__doc__!r}"
    assert ask_model() == 42
