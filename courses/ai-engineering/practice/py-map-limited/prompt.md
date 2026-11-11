# Run async work with a concurrency limit

You have 200 prompts to send to an LLM. Sending them one by one is slow; sending all 200 at once gets you rate-limited. The answer is "at most N at a time".

```python
async def map_limited(func: Callable[[T], Awaitable[R]], items: list[T], limit: int) -> list[R]:
```

- Call `await func(item)` for every item, running calls concurrently.
- Never have more than `limit` calls in progress at the same time. Use an `asyncio.Semaphore(limit)`.
- Return the results **in the same order as `items`** (not the order they finished). `asyncio.gather` keeps order for you.
- An empty list returns `[]`.

Example:

```python
async def double(x):
    await asyncio.sleep(0.01)
    return x * 2

asyncio.run(map_limited(double, [1, 2, 3, 4, 5], limit=2))   # [2, 4, 6, 8, 10]
```
