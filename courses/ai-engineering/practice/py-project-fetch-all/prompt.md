# Project part 2: fetch many, concurrently, and save a report

Now finish the client. `Post`, `Failure` and `fetch_one` from part 1 are already in the file (completed). Add:

```python
async def fetch_all(client: httpx.AsyncClient, urls: list[str], limit: int = 5) -> tuple[list[Post], list[Failure]]:
def write_report(posts: list[Post], failures: list[Failure], path: str | Path) -> None:
```

**`fetch_all`**

- Calls `fetch_one` for every URL, concurrently, with at most `limit` requests in flight (an `asyncio.Semaphore`).
- Splits the results into `(posts, failures)`. Each list keeps the order of `urls`.
- Never raises because one URL failed: that's what `Failure` is for.

**`write_report`** writes a JSON file shaped like this (2-space indent is nice but not required):

```json
{
  "posts": [{"id": 1, "user_id": 7, "title": "Hello", "body": "..."}],
  "failures": [{"url": "/posts/3", "error": "HTTP 404"}]
}
```

Use `model.model_dump()` for each item. Create the parent folder if it doesn't exist (`path.parent.mkdir(parents=True, exist_ok=True)`).

Example:

```python
posts, failures = await fetch_all(client, ["/posts/1", "/posts/2", "/posts/3"], limit=2)
write_report(posts, failures, "out/report.json")
```

When this passes, you have the whole project working. The project page explains how to move it into its own repository.
