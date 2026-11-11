# Project part 1: fetch and validate one resource

This is the first half of the week's project: an async client that fetches posts from a JSON API, validates them, and never crashes on bad responses. Here you build the model and the single-request function. In part 2 you'll run many of them concurrently.

A post from the API looks like this:

```json
{"id": 1, "userId": 7, "title": "Hello", "body": "First post"}
```

Write two models and one async function:

```python
class Post(BaseModel):
    id: int          # > 0
    user_id: int     # > 0, comes from the JSON key "userId"
    title: str       # at least 1 character
    body: str

class Failure(BaseModel):
    url: str
    error: str

async def fetch_one(client: httpx.AsyncClient, url: str) -> Post | Failure:
```

For `user_id`, use `Field(alias="userId", gt=0)` so Pydantic reads the camelCase key.

`fetch_one` sends `GET url` and **returns** (never raises) one of:

| What happened | Return |
|---|---|
| 2xx with a valid post | `Post` |
| 4xx or 5xx status | `Failure(url=url, error="HTTP <status>")`, e.g. `"HTTP 404"` |
| Network problem (`httpx.RequestError`: connection errors, timeouts) | `Failure(error="request failed: <ExceptionClassName>")` |
| Body is not JSON | `Failure(error="invalid JSON")` |
| JSON doesn't fit `Post` | `Failure(error="invalid data: <details>")` |

> **Note:** `pydantic.ValidationError` is a subclass of `ValueError`, and so is `json.JSONDecodeError`. Parse the JSON and validate it in separate steps (or catch `ValidationError` first) so you report the right error.

Check is offline: the tests use `httpx.MockTransport`.
