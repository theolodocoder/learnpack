import asyncio
from collections.abc import Awaitable, Callable


async def map_limited[T, R](func: Callable[[T], Awaitable[R]], items: list[T], limit: int) -> list[R]:
    """await func(item) for every item, at most `limit` at a time, results in input order."""
    sem = asyncio.Semaphore(limit)

    async def run_one(item: T) -> R:
        async with sem:
            return await func(item)

    return await asyncio.gather(*(run_one(item) for item in items))


if __name__ == "__main__":
    async def double(x):
        await asyncio.sleep(0.01)
        return x * 2

    print(asyncio.run(map_limited(double, [1, 2, 3, 4, 5], limit=2)))
