import functools
import time
from collections.abc import Callable


def retry(times: int = 3, base_delay: float = 0.5,
          retry_on: tuple[type[BaseException], ...] = (Exception,),
          sleep: Callable[[float], None] = time.sleep):
    """Retry the decorated function with exponential backoff."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # TODO: loop over attempts 0 .. times-1
            # TODO: try to return func(*args, **kwargs)
            # TODO: except retry_on: if it was the last attempt, re-raise (bare `raise`);
            #       otherwise sleep(base_delay * 2 ** attempt)
            return func(*args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    calls = 0

    @retry(times=3, base_delay=0.1, retry_on=(ConnectionError,), sleep=lambda s: print(f"sleeping {s}s"))
    def flaky():
        global calls
        calls += 1
        if calls < 3:
            raise ConnectionError("try again")
        return "ok"

    try:
        print(flaky(), "after", calls, "calls")
    except ConnectionError as e:
        print("gave up:", e)
