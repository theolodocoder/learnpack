# Run many calls, survive slow and failing ones

When you fan out to several APIs at once, one slow or broken call shouldn't sink the rest. Write a helper that runs awaitables concurrently, gives each a timeout, and reports what happened to every one.

```python
async def gather_settled(aws: list[Awaitable], timeout: float) -> list[tuple[str, object]]:
```

Return one tuple per awaitable, in the same order:

- `("ok", value)` if it finished within `timeout` seconds,
- `("timeout", None)` if it took longer,
- `("error", str(exc))` if it raised any other exception.

All awaitables run **concurrently**, so the total time is about the slowest one (capped at `timeout`), not the sum.

Hints: write a small `async def settle(aw)` that wraps one awaitable with `async with asyncio.timeout(timeout):` (or `asyncio.wait_for`) and a `try` / `except`. A timeout raises the built-in `TimeoutError`. Then `asyncio.gather` all the `settle(...)` calls.

Example:

```python
async def ok():   await asyncio.sleep(0.01); return "fast"
async def slow(): await asyncio.sleep(1);    return "never"
async def bad():  raise ValueError("boom")

asyncio.run(gather_settled([ok(), slow(), bad()], timeout=0.1))
# [('ok', 'fast'), ('timeout', None), ('error', 'boom')]
```
