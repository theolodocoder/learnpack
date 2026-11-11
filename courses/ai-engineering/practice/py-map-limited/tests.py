import asyncio
import time

from solution import map_limited


class Tracker:
    """An async function that records how many calls run at once."""

    def __init__(self, delay=0.02):
        self.delay = delay
        self.active = 0
        self.peak = 0

    async def __call__(self, x):
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(self.delay)
        self.active -= 1
        return x * 10


def test_returns_results_in_input_order():
    async def slow_for_small(x):
        await asyncio.sleep(0.05 - x * 0.01)  # small x finishes last
        return x

    got = asyncio.run(map_limited(slow_for_small, [1, 2, 3, 4], limit=4))
    assert got == [1, 2, 3, 4], f"expected input order [1, 2, 3, 4], got {got!r}"


def test_never_exceeds_the_limit():
    t = Tracker()
    got = asyncio.run(map_limited(t, list(range(10)), limit=3))
    assert got == [x * 10 for x in range(10)], f"wrong results: {got!r}"
    assert t.peak <= 3, f"up to {t.peak} calls ran at once, but the limit is 3"


def test_actually_runs_concurrently():
    # Peak concurrency proves the calls overlap; a wall-clock check would be flaky on a busy machine.
    t = Tracker(delay=0.05)
    asyncio.run(map_limited(t, list(range(6)), limit=3))
    assert t.peak == 3, f"expected 3 calls at once (they should overlap), saw at most {t.peak}"


def test_empty_list_returns_empty_list():
    got = asyncio.run(map_limited(Tracker(), [], limit=2))
    assert got == [], f"expected [], got {got!r}"
