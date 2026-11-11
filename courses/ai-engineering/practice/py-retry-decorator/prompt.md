# A retry decorator with backoff

LLM and HTTP calls fail now and then: rate limits, overloaded servers, dropped connections. The fix is to wait and try again, waiting longer each time. Write that once, as a decorator, and reuse it everywhere.

```python
def retry(times: int = 3, base_delay: float = 0.5,
          retry_on: tuple[type[BaseException], ...] = (Exception,),
          sleep: Callable[[float], None] = time.sleep):
```

`retry(...)` returns a decorator. A function decorated with it:

1. Is called up to `times` times in total.
2. If a call raises an exception that is an instance of one of `retry_on`, and attempts remain, it calls `sleep(delay)` and tries again. The delay doubles each time: `base_delay`, `base_delay * 2`, `base_delay * 4`, …
3. Exceptions **not** in `retry_on` are raised immediately, with no retry.
4. When all attempts fail, the last exception is raised (re-raised, not wrapped).
5. Returns the function's result as soon as a call succeeds.
6. Keeps the original function's `__name__` and docstring (use `functools.wraps`).

The `sleep` parameter exists so tests can pass a fake that records delays instead of really waiting.

Example:

```python
calls = 0

@retry(times=3, base_delay=0.1, retry_on=(ConnectionError,))
def flaky():
    global calls
    calls += 1
    if calls < 3:
        raise ConnectionError("try again")
    return "ok"

flaky()   # sleeps 0.1, then 0.2, then returns 'ok'
```
