import time
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def timer(label: str, log: list[dict] | None = None) -> Iterator[dict]:
    """Time the with-block. Fills in result['seconds'] even if the block raises."""
    result = {"label": label, "seconds": None}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["seconds"] = time.perf_counter() - start
        if log is not None:
            log.append(result)


if __name__ == "__main__":
    log = []
    with timer("call model", log) as t:
        time.sleep(0.05)
    print(t)
    print(log)
