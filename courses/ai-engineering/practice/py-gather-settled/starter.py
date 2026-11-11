import asyncio
from collections.abc import Awaitable


async def gather_settled(aws: list[Awaitable], timeout: float) -> list[tuple[str, object]]:
    """Run all awaitables concurrently; report ('ok', v), ('timeout', None) or ('error', msg) for each."""

    async def settle(aw: Awaitable) -> tuple[str, object]:
        # TODO: async with asyncio.timeout(timeout): value = await aw
        # TODO: except TimeoutError -> ("timeout", None); except Exception as e -> ("error", str(e))
        return ("ok", await aw)

    # TODO: gather settle(aw) for every aw
    return []


if __name__ == "__main__":
    async def ok():
        await asyncio.sleep(0.01)
        return "fast"

    async def slow():
        await asyncio.sleep(1)
        return "never"

    async def bad():
        raise ValueError("boom")

    print(asyncio.run(gather_settled([ok(), slow(), bad()], timeout=0.1)))
