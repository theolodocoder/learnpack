import asyncio
import time

from solution import gather_settled


async def value_after(v, delay):
    await asyncio.sleep(delay)
    return v


async def fail(msg):
    await asyncio.sleep(0)
    raise ValueError(msg)


def test_all_ok_results_in_order():
    got = asyncio.run(gather_settled([value_after("a", 0.03), value_after("b", 0.01)], timeout=1))
    want = [("ok", "a"), ("ok", "b")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_slow_call_reports_timeout():
    got = asyncio.run(gather_settled([value_after("fast", 0.01), value_after("slow", 2)], timeout=0.1))
    want = [("ok", "fast"), ("timeout", None)]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_failing_call_reports_error_message():
    got = asyncio.run(gather_settled([fail("boom"), value_after(1, 0)], timeout=1))
    want = [("error", "boom"), ("ok", 1)]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_runs_concurrently():
    start = time.perf_counter()
    asyncio.run(gather_settled([value_after(i, 0.1) for i in range(5)], timeout=1))
    elapsed = time.perf_counter() - start
    # Run one after another they'd take 0.5 s; the margin keeps this stable on a busy machine.
    assert elapsed < 0.45, f"five 0.1 s calls should run together in about 0.1 s, took {elapsed:.2f} s"


def test_empty_list():
    got = asyncio.run(gather_settled([], timeout=1))
    assert got == [], f"expected [], got {got!r}"
