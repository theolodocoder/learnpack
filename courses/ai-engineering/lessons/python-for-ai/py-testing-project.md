# Testing, then the week 1 build

## Why this matters

LLM apps are full of code that's easy to break silently: a prompt builder that drops the context, a parser that crashes on one odd response, a retry loop that never stops. Tests are how you change code with confidence, and later in the course you'll extend the same idea to **evals**, which test the model's behaviour. Clients hiring for AI work look at whether a repo has tests; it's the quickest signal that you ship reliable code. This lesson covers pytest-style testing, then you'll build the week's project in three steps.

## pytest in one page

[pytest](https://docs.pytest.org/) is the standard Python test runner. Its style is minimal: tests are plain functions whose names start with `test_`, and checks are plain `assert` statements.

```python
# text_utils.py
def truncate(text: str, limit: int) -> str:
    """Cut text to at most `limit` characters, adding '…' if it was cut."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"
```

```python
# test_text_utils.py
import pytest
from text_utils import truncate

def test_short_text_is_unchanged():
    assert truncate("hi", 10) == "hi"

def test_long_text_is_cut_with_ellipsis():
    assert truncate("hello world", 5) == "hell…"

def test_result_never_exceeds_limit():
    assert len(truncate("x" * 100, 7)) == 7

def test_rejects_zero_limit():
    with pytest.raises(ValueError):
        truncate("hi", 0)
```

Install pytest in your venv (`uv pip install pytest`) and run `pytest` from the project folder. It finds files named `test_*.py`, runs every `test_*` function, and reports passes and failures. When an `assert` fails, pytest shows the values on both sides, so `assert got == want` is usually all you need.

Conventions that make tests useful:

- **Name tests after the behaviour**, as a sentence: `test_rejects_zero_limit`, not `test_truncate_2`. When it fails, the name tells you what broke. (The Check button shows test names this way too.)
- **One behaviour per test.** Several small tests beat one large one: a failure points straight at the problem.
- **Test files mirror code files**: `text_utils.py` → `test_text_utils.py`, usually in a `tests/` folder.

### Arrange, act, assert

Most tests have the same three parts. Keep them visibly separate:

```python
def test_parse_users_reports_bad_rows():
    # Arrange: build the input
    rows = [{"name": "Ada", "age": 36, "email": "ada@example.com"}, {"name": "", "age": -1}]
    # Act: call the code under test, once
    users, errors = parse_users(rows)
    # Assert: check the outcome
    assert len(users) == 1
    assert errors[0].startswith("row 2:")
```

If the arrange step gets long, move it into a helper function (or a pytest **fixture**, a function pytest calls to provide test inputs, which you'll meet in later sections).

### Testing the edge cases

Normal inputs are the easy part. Bugs hide at the edges, so for each function ask:

- **Empty:** empty string, empty list, zero items, `None` where allowed.
- **Boundaries:** exactly at a limit, one below, one above (`limit=1`, length equal to `limit`).
- **Bad input:** wrong type, negative numbers, malformed JSON, missing keys. Does it raise the right exception, or return a clear failure?
- **Odd but valid:** unicode and emoji, very long strings, duplicates, whitespace.
- **External failures:** for code that calls APIs: 404, 500, timeouts, invalid JSON, a valid response with the wrong shape.

A good test would **fail if the code were wrong**. A test that passes for both the correct and a broken implementation proves nothing. The first exercise in this lesson grades exactly that: your tests are run against deliberately broken versions of a function, and must catch each one.

### Parametrize repetitive tests

When the same check runs over many inputs, `pytest.mark.parametrize` avoids copy-paste:

```python
import pytest

@pytest.mark.parametrize("text, limit, want", [
    ("hi", 10, "hi"),
    ("hello", 5, "hello"),       # exactly at the limit
    ("hello!", 5, "hell…"),      # one over
])
def test_truncate(text, limit, want):
    assert truncate(text, limit) == want
```

Each tuple becomes its own test case in the report.

### Testing code that does I/O

Tests must be **fast, offline and deterministic**: same result every run, no network, no real API keys, no sleeping. That's why code in this course is shaped so dependencies can be swapped:

- HTTP functions take an `httpx.Client` / `AsyncClient`; tests pass one with `httpx.MockTransport`.
- Functions that sleep take a `sleep` parameter; tests pass a fake that records delays.
- Functions that read config take the environment or a path; tests pass a dict or a temporary file (`tempfile.mkdtemp()`, or pytest's `tmp_path` fixture).
- Code that calls Claude takes a `client`; tests pass a fake client that returns scripted replies.

For async functions, a test can simply call `asyncio.run(...)`:

```python
import asyncio, httpx

def test_fetch_one_reports_404():
    async def go():
        transport = httpx.MockTransport(lambda request: httpx.Response(404))
        async with httpx.AsyncClient(base_url="https://api.example.com", transport=transport) as client:
            return await fetch_one(client, "/posts/99")

    result = asyncio.run(go())
    assert result.error == "HTTP 404"
```

(The `pytest-asyncio` plugin lets you write `async def test_...` directly; `asyncio.run` needs no plugin.)

## The week 1 build: an async API client

Time to combine the whole week. You'll build a small but production-shaped client that:

1. fetches several JSON endpoints **concurrently** with `httpx.AsyncClient`,
2. never has more than N requests in flight (`asyncio.Semaphore`),
3. **validates** every response with a Pydantic model,
4. **collects failures** (HTTP errors, network errors, invalid JSON, wrong shape) instead of crashing,
5. writes the results to a JSON report.

This is the skeleton of a lot of real AI work: an evaluation runner that sends 300 prompts and saves every result, an ingestion job that pulls documents from an API before embedding them, an agent tool that calls several services at once.

The data comes from a posts API shaped like this:

```json
{"id": 1, "userId": 7, "title": "Hello", "body": "First post"}
```

### Design: return failures as values

The key design decision is that `fetch_one` **returns** either a `Post` or a `Failure`; it never raises for a bad URL:

```python
from pydantic import BaseModel, Field

class Post(BaseModel):
    id: int = Field(gt=0)
    user_id: int = Field(alias="userId", gt=0)
    title: str = Field(min_length=1)
    body: str

class Failure(BaseModel):
    url: str
    error: str
```

If `fetch_one` raised, one bad URL would abort a `gather` of hundreds. Returning a `Failure` turns errors into data that you can count, log and report. The return type `Post | Failure` makes callers handle both, and `isinstance(result, Post)` tells them apart.

`fetch_one` has several distinct failure points, and each needs its own handling. Order matters:

```python
async def fetch_one(client, url):
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:      # got a response, but 4xx/5xx
        return Failure(url=url, error=f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:         # no response at all
        return Failure(url=url, error=f"request failed: {type(e).__name__}")
    # ...then parse JSON (ValueError on failure), then validate (ValidationError)
```

Keep JSON parsing and validation in separate `try` blocks: both errors are `ValueError` subclasses, and you want to report them differently.

### Concurrency with a limit

`fetch_all` is the semaphore-plus-gather pattern from the async lesson, followed by splitting the results:

```python
results = await asyncio.gather(*(limited(url) for url in urls))
posts = [r for r in results if isinstance(r, Post)]
failures = [r for r in results if isinstance(r, Failure)]
```

`gather` preserves input order, so both lists come out in URL order, which makes reports easy to compare between runs.

### Writing the report

`model_dump()` turns each model into a dict that `json.dumps` can serialise. Create the output folder if needed, and write with an explicit encoding:

```python
report = {"posts": [p.model_dump() for p in posts], "failures": [f.model_dump() for f in failures]}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
```

### The steps

The practice below builds it in order, each step on top of the last:

1. **Write tests that catch bugs.** Practise the testing ideas on a small function.
2. **Project part 1:** the `Post` and `Failure` models and `fetch_one`.
3. **Project part 2:** `fetch_all` with a concurrency limit, and `write_report`.

Every test uses `httpx.MockTransport`, including an async handler that tracks how many requests are in flight at once, so the concurrency limit is actually checked. When both parts pass, read the project brief for how to turn this into a standalone repo with its own pytest suite.

> **Try it:** After part 2 passes, point the demo at the real `https://jsonplaceholder.typicode.com` with a normal `httpx.AsyncClient(base_url=..., timeout=10)` (no transport) and Run it for `/posts/1` to `/posts/20`, plus `/posts/9999` to see a real 404 land in `failures`.

## Common mistakes

- **Tests that can't fail.** `assert result` passes for any non-empty value. Compare against the exact expected value.
- **Testing only the happy path.** Most real bugs are in the empty, boundary and error cases.
- **Tests that need the network or a key.** They're slow and flaky, and they fail on CI. Inject fakes.
- **One giant test.** When it fails, you don't know which behaviour broke.
- **Raising inside a fan-out.** One exception in `gather` loses the other results. Return failures as values (or use `return_exceptions=True`).
- **Catching `ValueError` around both `.json()` and validation.** You can't tell "not JSON" from "wrong shape". Separate the steps.

## Recap

- pytest: `test_*` functions, plain `assert`, `pytest.raises` for expected exceptions, `parametrize` for many inputs.
- Name tests after behaviour; arrange, act, assert; one behaviour per test.
- Always test empty, boundary, bad-input and external-failure cases; a good test fails on broken code.
- Keep tests offline and deterministic by injecting clients, transports, sleep functions and config.
- The week 1 build: `fetch_one` returns `Post | Failure`, `fetch_all` runs with a semaphore and splits results, `write_report` saves JSON with `model_dump()`.
