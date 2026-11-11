# Week 1 build: an async API client

## The goal

Build a small, production-shaped Python client that fetches many JSON resources at once and never falls over:

- fetches a list of URLs **concurrently** with `httpx.AsyncClient`,
- keeps at most N requests in flight with an `asyncio.Semaphore`,
- **validates** every response with a Pydantic model,
- **collects failures** (HTTP errors, network errors, invalid JSON, wrong shape) as data instead of crashing,
- writes posts and failures to a JSON report.

It's the same skeleton you'll reuse all course: evaluation runners, document ingestion jobs and agent tools are all "call many things concurrently, validate, record what failed".

## Build it in the platform first

You write the code in the practice of the last lesson, **Testing, then the week 1 build**:

1. **Write tests that catch bugs:** warm up your testing skills.
2. **Project part 1:** `Post` and `Failure` models and `fetch_one`.
3. **Project part 2:** `fetch_all` with a concurrency limit, and `write_report`.

Get all checks green there before moving on.

## Then make it a real repo

A project only counts for your portfolio when it lives in its own repository and someone else can run it. Move your code out of the platform:

1. Create a new folder and Git repository, e.g. `async-api-client`, with a venv (`uv venv`) and a `requirements.txt` listing `httpx`, `pydantic` and `pytest`.
2. Put the code in a module, for example `client.py`, with a `main()` that fetches `https://jsonplaceholder.typicode.com/posts/1` … `/posts/20` plus one URL that 404s, and writes `report.json`. Run it with `python client.py`.
3. Read the base URL and concurrency limit from environment variables (with defaults), loading a `.env` with `python-dotenv`. Commit a `.env.example`, never a `.env`.
4. Add `tests/test_client.py` with pytest tests that use `httpx.MockTransport`: a valid post, a 404, a network error, invalid JSON, wrong shape, the concurrency limit, and the report file. No test may touch the network. `pytest` must pass.
5. Write a `README.md`: what it does, how to install, how to run, how to test, and an example of the report output.
6. Push it to GitHub.

## Stretch goals

- Retry 429 and 5xx responses with exponential backoff (reuse your `retry` idea, but async: `await asyncio.sleep`).
- Add a command-line interface with `argparse`: `python client.py --limit 10 --out out/report.json URL...`.
- Time the whole run with your timer context manager and print a summary: posts fetched, failures by error type, seconds taken.
- Add a GitHub Actions workflow that runs `pytest` on every push.
