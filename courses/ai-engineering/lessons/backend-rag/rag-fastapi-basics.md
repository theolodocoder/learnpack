# FastAPI fundamentals

## Why this matters

Almost every paid AI job ends in an HTTP API. The chatbot on a company's website, the "summarise this ticket" button in a support tool, the mobile app that answers questions about a PDF: all of them talk to a backend, and the backend talks to the LLM. FastAPI is the most popular way to build that backend in Python, and it's built on two things you already know: type hints and Pydantic. Learn it well once and every project from here on has a front door.

## 1. Why a backend sits between users and the LLM

You could, in theory, call Claude straight from a browser or a mobile app. Don't. Anything shipped to a user's device can be read by that user, so your `ANTHROPIC_API_KEY` would be public within minutes and someone else would run up your bill.

A backend gives you a place to:

- **Keep secrets server-side.** The key lives in an environment variable on your server. Clients never see it.
- **Validate input.** Reject a 2 MB "question", an empty message, or a malformed request before it costs you tokens.
- **Control cost and abuse.** Rate-limit per user, cap `max_tokens`, choose the model yourself instead of letting the client pick the most expensive one.
- **Add your own logic.** Look up the user's documents, build the prompt, call tools, log usage, cache answers. This is where retrieval-augmented generation (RAG) will live later in this section.
- **Map failures to sensible responses.** A rate limit from the LLM provider becomes a polite "try again in a moment", not a stack trace.

```
browser / app  ──HTTP──▶  your FastAPI backend  ──HTTPS + API key──▶  Claude API
                          (validation, auth,                          (and later:
                           prompts, retrieval)                         embeddings, DB)
```

## 2. Your first app

Install FastAPI with its standard extras (they include the `uvicorn` server and the `fastapi` command-line tool):

```bash
pip install "fastapi[standard]"
```

A complete app, saved as `main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Notes API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
```

Run it in development mode, which restarts the server whenever you save a file:

```bash
fastapi dev main.py
# Serving at: http://127.0.0.1:8000
# API docs:   http://127.0.0.1:8000/docs
```

Open `http://127.0.0.1:8000/health` and you'll see `{"status":"ok"}`. Open `/docs` and you get interactive documentation generated from your code, where you can try every endpoint from the browser. You get that page for free because FastAPI reads your type hints.

Under the hood, `fastapi dev` runs **uvicorn**, an ASGI server (the program that actually listens on a port and hands requests to your app). In production you'd use `fastapi run main.py`, or call uvicorn directly: `uvicorn main:app --host 0.0.0.0 --port 8000`. `main:app` means "the `app` object inside `main.py`".

The pieces:

- `@app.get("/health")` registers a **route**: an HTTP method plus a path. There's `@app.post`, `@app.put`, `@app.patch` and `@app.delete` too.
- The decorated function is called a **path operation function** (or handler). Whatever it returns is converted to JSON.

## 3. Path and query parameters

Parameters come from the URL in two ways:

```python
@app.get("/notes/{note_id}")
def get_note(note_id: int, verbose: bool = False) -> dict:
    return {"note_id": note_id, "verbose": verbose}
```

- `note_id` appears in the path template `{note_id}`, so it's a **path parameter**. `GET /notes/42` gives `note_id=42`.
- `verbose` isn't in the path, so it's a **query parameter**: `GET /notes/42?verbose=true`. Because it has a default, it's optional.

The type hints do real work. `note_id: int` means `GET /notes/abc` is rejected automatically with a **422 Unprocessable Content** response explaining what was wrong. Your function only ever runs with valid data.

To add constraints, use `Query` (or `Path`) inside `Annotated`:

```python
from typing import Annotated
from fastapi import Query


@app.get("/search")
def search(q: str, limit: Annotated[int, Query(ge=1, le=50)] = 10) -> dict:
    return {"q": q, "limit": limit}
```

`GET /search?q=refund&limit=500` now returns 422, because `limit` must be between 1 and 50. That one line protects you from a client asking for a million results.

## 4. Request and response bodies with Pydantic

For `POST` and `PUT`, data arrives as a JSON body. Describe it with a Pydantic model, exactly as you did in *Type hints and Pydantic*:

```python
from pydantic import BaseModel, Field


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str = ""


class Note(NoteIn):
    id: int


notes: dict[int, Note] = {}


@app.post("/notes", status_code=201)
def create_note(note: NoteIn) -> Note:
    new = Note(id=len(notes) + 1, **note.model_dump())
    notes[new.id] = new
    return new
```

What FastAPI does for you here:

1. Reads the request body as JSON.
2. Validates it against `NoteIn`. An empty title or a missing field gives a 422 with details; your function never sees bad data.
3. Calls `create_note` with a real `NoteIn` instance.
4. Validates and serialises the return value using the **return type** `Note`. This is your **response model**. If you return extra fields that aren't in the model, they're filtered out, which is how you avoid leaking things like password hashes.

`status_code=201` sets the success code. Use **201 Created** when a POST creates something, **200 OK** for normal reads, **204 No Content** for a delete that returns nothing.

How FastAPI decides where each parameter comes from:

| Parameter looks like | Comes from |
|---|---|
| name appears in the path `{...}` | path |
| simple type (`int`, `str`, `bool`...) not in the path | query string |
| a Pydantic model | JSON body |
| `Annotated[str, Header()]` | an HTTP header |

## 5. Errors with `HTTPException`

When something goes wrong that's the client's fault, or a resource doesn't exist, raise `HTTPException`:

```python
from fastapi import HTTPException


@app.get("/notes/{note_id}")
def read_note(note_id: int) -> Note:
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    return notes[note_id]
```

The client receives status 404 and the body `{"detail": "Note not found"}`. Raising (not returning) matters: it stops the function immediately, even from deep inside a helper.

The status codes you'll use most:

| Code | Meaning | Typical cause |
|---|---|---|
| 200 / 201 / 204 | OK / Created / No Content | success |
| 400 | Bad Request | input is valid JSON but makes no sense |
| 401 | Unauthorized | missing or wrong credentials |
| 403 | Forbidden | logged in, but not allowed |
| 404 | Not Found | no such resource |
| 422 | Unprocessable Content | failed validation (FastAPI sends this for you) |
| 429 | Too Many Requests | the client hit your rate limit |
| 500 | Internal Server Error | a bug in your code |
| 502 / 503 / 504 | Bad Gateway / Unavailable / Timeout | something *you* depend on (like the LLM) failed |

The 4xx codes say "the client should change something"; 5xx codes say "the server has a problem". Getting this right lets front-end developers and monitoring tools do the right thing.

## 6. Dependency injection with `Depends`

Many endpoints need the same things: the current settings, a database connection, an LLM client, the authenticated user. Instead of creating them inside every handler, you declare them as **dependencies**:

```python
import os
import secrets
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel


class Settings(BaseModel):
    api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings(api_key=os.environ.get("APP_API_KEY", ""))


def require_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_key or not secrets.compare_digest(x_api_key or "", settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/private", dependencies=[Depends(require_api_key)])
def private() -> dict:
    return {"secret": "only for key holders"}
```

How to read this:

- `Depends(get_settings)` tells FastAPI: "before calling me, call `get_settings()` and pass me the result." `lru_cache` makes it build the settings once and reuse them.
- Dependencies can depend on other dependencies. `require_api_key` needs settings *and* a header; FastAPI works out the order.
- `Header()` reads an HTTP header. FastAPI converts the underscore to a hyphen, so `x_api_key` reads the `X-API-Key` header.
- `dependencies=[...]` on the decorator runs the dependency for its side effect (raising 401) without passing a value to the handler. To use the value, put it in the parameters instead: `settings: Settings = Depends(get_settings)`.
- `secrets.compare_digest` compares in constant time, so an attacker can't guess the key one character at a time by measuring response times.

The real payoff is **testing**. Because the handler asks for its dependencies instead of building them, a test can swap any of them out:

```python
app.dependency_overrides[get_settings] = lambda: Settings(api_key="test-key")
```

You'll use exactly this trick in the next lesson to replace the real Claude client with a fake one.

## 7. Testing with `TestClient`

`TestClient` calls your app in-process: no server, no port, no network. It has the same interface as `httpx` (`.get`, `.post`, `json=`, `headers=`), which you met in *HTTP and JSON with httpx*.

```python
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_and_read_note():
    r = client.post("/notes", json={"title": "Groceries", "body": "rice, beans"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Groceries"


def test_empty_title_is_rejected():
    r = client.post("/notes", json={"title": ""})
    assert r.status_code == 422


def test_private_needs_key():
    app.dependency_overrides[get_settings] = lambda: Settings(api_key="k")
    assert client.get("/private").status_code == 401
    assert client.get("/private", headers={"X-API-Key": "k"}).status_code == 200
    app.dependency_overrides.clear()
```

Run these with `pytest` as you learned in *Testing, then the week 1 build*. Test status codes *and* bodies, test the failure paths, and always clear `dependency_overrides` afterwards so one test doesn't leak into the next.

> **Try it:** In the first exercise below, Run the starter, then add a `print(client.get("/notes?limit=0").json())` to see what FastAPI's 422 body looks like.

## 8. Sync or async handlers?

You can write handlers with `def` or `async def`. The rule:

- Use **`async def`** when the handler awaits async I/O: `AsyncAnthropic`, `httpx.AsyncClient`, async database drivers. This is the normal case for LLM backends, and the next lesson's topic.
- Use plain **`def`** when the handler calls blocking code (a sync library, `time.sleep`, `requests`). FastAPI runs `def` handlers in a thread pool so they don't block the event loop.
- **Never** call blocking code inside `async def`. One slow blocking call freezes every other request on that worker.

## Common mistakes

- **Putting the API key in front-end code** "just for the demo". It will leak.
- **Returning error dictionaries with status 200**, like `return {"error": "not found"}`. Clients and monitoring can't tell it failed. Raise `HTTPException` with the right code.
- **Mutable global state in tests.** A module-level `notes` dict keeps its contents between tests. Clear it, or build state through a dependency you can override.
- **Forgetting `app.dependency_overrides.clear()`**, so an override from one test silently affects the next.
- **Blocking calls inside `async def` handlers**, such as the sync `anthropic.Anthropic()` client. Use the async client, or a `def` handler.
- **No limits on inputs.** Always set `max_length` on free text and bounds on numbers like `limit`.

## Recap

- A backend keeps the LLM key secret and is where validation, auth, limits, prompts and retrieval live.
- Routes are decorated functions; path parameters come from `{...}` in the path, simple typed parameters from the query string, Pydantic models from the JSON body.
- The return type is the response model; `status_code=` sets the success code; `HTTPException` sends errors.
- FastAPI returns 422 for invalid input automatically.
- `Depends` injects shared things (settings, clients, auth), and `app.dependency_overrides` swaps them in tests.
- `TestClient` tests the whole app in-process. `fastapi dev main.py` runs it locally with auto-reload and docs at `/docs`.
