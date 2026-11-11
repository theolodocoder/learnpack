# HTTP and JSON with httpx

## Why this matters

Every LLM API, vector database, payment provider and SaaS tool you'll integrate is an HTTP API that speaks JSON. The Claude SDK is a convenient wrapper around HTTP requests, and when something goes wrong (a 429, a 400, a timeout) you'll debug it in HTTP terms. Agents call tools that are often HTTP APIs, and the backends you'll build in later sections **are** HTTP APIs. This lesson gives you the vocabulary and the client library, `httpx`, plus the trick that makes this code testable without a network.

## HTTP in five minutes

An HTTP exchange is one **request** from a client and one **response** from a server.

A request has:

- a **method**, saying what you want to do:
  - `GET`: read something. No body.
  - `POST`: create something or trigger an action (most LLM API calls are POSTs).
  - `PUT` / `PATCH`: replace / partly update something.
  - `DELETE`: remove something.
- a **URL**: `https://api.example.com/v1/users/42?include=posts`. The path (`/v1/users/42`) names the resource; the **query string** after `?` holds optional parameters as `key=value` pairs joined by `&`.
- **headers**: metadata as `Name: value` lines. The important ones: `Authorization` (credentials), `Content-Type` (format of the body, e.g. `application/json`), `Accept`, `User-Agent`.
- an optional **body**: for APIs, usually a JSON document.

A response has a **status code**, headers and a body. The status code's first digit tells you the category:

| Code | Meaning | What to do |
|---|---|---|
| 200 OK, 201 Created, 204 No Content | Success | Use the body (204 has none) |
| 301, 302, 307, 308 | Redirect | Follow it (httpx won't unless you ask) |
| 400 Bad Request | Your request is malformed | Fix your code; don't retry |
| 401 Unauthorized / 403 Forbidden | Missing or bad credentials / not allowed | Check your key; don't retry |
| 404 Not Found | No such resource | Often a normal "doesn't exist" answer |
| 422 Unprocessable Entity | Valid JSON, invalid content | Fix the data (FastAPI uses this for validation errors) |
| 429 Too Many Requests | Rate limited | Wait and retry (check the `Retry-After` header) |
| 500, 502, 503, 504 | Server-side failure | Usually temporary: retry with backoff |

Anthropic also uses **529 Overloaded**, which you should treat like a 503. The rule of thumb: **4xx means you did something wrong** (except 429), **5xx means they did**; retry 429 and 5xx, not other 4xx.

## httpx basics

`httpx` is a modern HTTP client with a `requests`-like API, plus async support, timeouts by default and HTTP/2. The Claude SDK itself is built on it.

```python
import httpx

response = httpx.get("https://httpbin.org/get", params={"q": "llm", "limit": 5})
print(response.status_code)          # 200
print(response.url)                  # https://httpbin.org/get?q=llm&limit=5
print(response.headers["content-type"])
data = response.json()               # parse the JSON body into Python objects
print(data["args"])                  # {'limit': '5', 'q': 'llm'}
```

Pass query parameters as a dict with `params=`; httpx encodes them correctly (spaces, `&`, unicode) so you never build query strings by hand. Note that values arrive at the server as strings.

Sending JSON is just as direct: `json=` serialises the object and sets `Content-Type: application/json` for you.

```python
response = httpx.post(
    "https://httpbin.org/post",
    json={"model": "claude-haiku-5-5", "messages": [{"role": "user", "content": "Hi"}]},
    headers={"Authorization": "Bearer my-token"},
)
print(response.json()["json"]["model"])   # claude-haiku-5-5
```

Useful response attributes: `.status_code`, `.headers`, `.text` (body as a string), `.content` (raw bytes), `.json()`, `.is_success`, `.url`, `.request`.

### Raising on errors

httpx does **not** raise an exception for a 404 or a 500; you get a normal response object with that status. Call `raise_for_status()` to turn 4xx/5xx into an `httpx.HTTPStatusError`:

```python
response = httpx.get("https://httpbin.org/status/404")
print(response.status_code)          # 404, no exception yet
try:
    response.raise_for_status()
except httpx.HTTPStatusError as err:
    print("failed:", err.response.status_code)   # failed: 404
```

The exception carries `err.request` and `err.response`, so you can branch on `err.response.status_code`. There's a second family of errors for when there's no response at all: `httpx.RequestError` and its subclasses, such as `httpx.ConnectError` (couldn't connect) and `httpx.TimeoutException` (took too long). A robust caller handles both:

```python
def fetch(client: httpx.Client, url: str) -> dict | None:
    try:
        response = client.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as err:
        print(f"HTTP {err.response.status_code} for {url}")
    except httpx.RequestError as err:
        print(f"request failed for {url}: {type(err).__name__}")
    return None
```

### Clients and timeouts

The top-level `httpx.get` opens a new connection each time. For real code, create one `httpx.Client` and reuse it: it keeps connections open (much faster for many requests), and holds shared settings like the base URL, headers and timeout. Use it as a context manager so connections are closed:

```python
import httpx

with httpx.Client(
    base_url="https://api.example.com/v1",
    headers={"Authorization": "Bearer my-token"},
    timeout=10.0,
) as client:
    r = client.get("/users/42")       # https://api.example.com/v1/users/42
```

**Always think about timeouts.** httpx defaults to 5 seconds, which is too short for LLM calls (a long answer can take a minute) and fine for most small APIs. `timeout=10.0` sets every phase; `httpx.Timeout(60.0, connect=5.0)` sets a long overall timeout but gives up quickly if the server can't even be reached. `timeout=None` disables timeouts entirely, which is how programs end up hanging forever.

### The async client

`httpx.AsyncClient` has the same API, with `await`. Combined with the previous lesson, this is how you fetch many URLs at once:

```python
import asyncio
import httpx

async def fetch_json(client: httpx.AsyncClient, path: str) -> dict:
    response = await client.get(path)
    response.raise_for_status()
    return response.json()

async def main():
    async with httpx.AsyncClient(base_url="https://jsonplaceholder.typicode.com", timeout=10) as client:
        posts = await asyncio.gather(*(fetch_json(client, f"/posts/{i}") for i in range(1, 6)))
    for p in posts:
        print(p["id"], p["title"][:40])

asyncio.run(main())
```

One `AsyncClient` is shared across all tasks; it's safe and efficient to do so.

## Testing HTTP code with `MockTransport`

Tests that hit real APIs are slow, flaky, cost money and fail when you're offline. httpx has a clean solution: a client's **transport** is the part that actually sends bytes over the network, and `httpx.MockTransport` replaces it with a Python function that receives the `httpx.Request` and returns an `httpx.Response`. Everything else (base URL, params, headers, `raise_for_status`, `.json()`) works exactly as in production.

```python
import httpx

def handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/users/1":
        return httpx.Response(200, json={"id": 1, "name": "Ada"})
    return httpx.Response(404, json={"error": "not found"})

client = httpx.Client(base_url="https://api.example.com", transport=httpx.MockTransport(handler))
print(client.get("/users/1").json())          # {'id': 1, 'name': 'Ada'}
print(client.get("/users/2").status_code)     # 404
```

The handler can inspect everything your code sent, which is how tests check that you used the right method, path, params and headers:

```python
seen = []

def recording_handler(request: httpx.Request) -> httpx.Response:
    seen.append(request)
    return httpx.Response(200, json=[])

client = httpx.Client(base_url="https://api.example.com", transport=httpx.MockTransport(recording_handler))
client.get("/search", params={"q": "rag"}, headers={"Authorization": "Bearer t"})
req = seen[0]
print(req.method, req.url.path, dict(req.url.params), req.headers["authorization"])
# GET /search {'q': 'rag'} Bearer t
```

To simulate a network failure, raise from the handler: `raise httpx.ConnectError("refused", request=request)`. For an `AsyncClient`, the handler may be a normal function or an `async def` (useful to `await asyncio.sleep(...)` and simulate slow servers).

The design lesson here matters more than the API: **functions that make HTTP calls should accept a client (or a transport) as a parameter** instead of creating one inside. Production code passes a real client; tests pass a mock. Every HTTP exercise in this course is shaped that way, and the Claude exercises in later sections do the same with a fake Claude client.

> **Try it:** In the fetch exercise's demo, change the handler to return `httpx.Response(500)` for every request and Run. Watch which of your functions raise and which return `None`.

## Config and keys from the environment

API keys and environment-specific settings (base URLs, timeouts) belong in **environment variables**, never in code. During development they come from a `.env` file, loaded with `python-dotenv`:

```python
# .env  (git-ignored)
# WEATHER_API_KEY=abc123
# WEATHER_API_URL=https://api.weather.example

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def make_client(env=os.environ) -> httpx.Client:
    key = env.get("WEATHER_API_KEY")
    if not key:
        raise RuntimeError("WEATHER_API_KEY is not set; add it to .env")
    return httpx.Client(
        base_url=env.get("WEATHER_API_URL", "https://api.weather.example"),
        headers={"Authorization": f"Bearer {key}"},
        timeout=10.0,
    )
```

Two habits in that snippet:

- **Fail fast with a clear message** when a required variable is missing. A `RuntimeError` naming the variable at startup is much better than a confusing 401 later.
- **Take the environment as a parameter** (defaulting to `os.environ`) so tests can pass a plain dict.

`os.environ["NAME"]` raises `KeyError` if missing; `os.environ.get("NAME", default)` returns a default. Environment variables are always strings, so convert numbers yourself: `int(os.environ.get("MAX_CONCURRENCY", "5"))`.

The Claude SDK follows the same convention: `anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from the environment.

## Common mistakes

- **Not checking the status.** httpx returns 4xx/5xx responses without raising. Call `raise_for_status()` or check `status_code` before using the body.
- **Calling `.json()` on an error page.** A 502 from a proxy is often HTML; `.json()` then raises a `ValueError`. Check the status first.
- **Building query strings by hand** with f-strings. Use `params=`; it encodes properly.
- **Creating a new client per request.** Reuse one client (as a context manager) for connection pooling.
- **No timeout, or the default 5 s for slow LLM endpoints.** Choose a timeout deliberately.
- **Hard-coded keys, or keys in URLs.** Keys go in headers and come from the environment.
- **Tests that use the real network.** Inject a client with `MockTransport`.

## Recap

- HTTP: method + URL (+ query params) + headers + optional JSON body → status code + headers + body.
- 2xx success; 4xx your fault (don't retry, except 429); 5xx and 529 their fault (retry with backoff).
- httpx: `client.get(path, params=...)`, `client.post(path, json=...)`, `response.json()`, `response.raise_for_status()`.
- Handle `httpx.HTTPStatusError` (bad status) and `httpx.RequestError` (no response) separately.
- Reuse one `Client`/`AsyncClient` with a `base_url`, headers and a deliberate timeout.
- Test with `httpx.MockTransport`: write functions that accept a client.
- Read keys and settings from the environment (`load_dotenv()` + `os.environ`), and fail fast when they're missing.
