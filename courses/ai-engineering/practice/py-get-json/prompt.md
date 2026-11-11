# Fetch JSON with httpx

Write two small functions that talk to a JSON API through an `httpx.Client`. The client is passed in, so the tests can give you one backed by `httpx.MockTransport` (no network needed).

```python
def get_json(client: httpx.Client, path: str, params: dict | None = None) -> dict:
def get_user_or_none(client: httpx.Client, user_id: int) -> dict | None:
```

**`get_json`**

- Sends `GET path` with the query `params` (let httpx encode them: `client.get(path, params=params)`).
- Raises `httpx.HTTPStatusError` for any 4xx/5xx response (`response.raise_for_status()`).
- Returns the parsed JSON body.

**`get_user_or_none`**

- Calls `GET /users/{user_id}` (reuse `get_json`).
- Returns `None` if the server says **404**.
- Lets every other error propagate (a 500 is not "no such user").

Example, with a client whose `base_url` is `https://api.example.com`:

```python
get_json(client, "/search", params={"q": "llm", "limit": 2})
# sends GET https://api.example.com/search?q=llm&limit=2
get_user_or_none(client, 999)   # None when the API returns 404
```

The demo in the starter builds a mock API so you can Run it offline.
