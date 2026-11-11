# Serving Claude from FastAPI

## Why this matters

The single most common AI backend endpoint is "take the user's message, call the model, send back the answer". Doing it properly means: not blocking the server while Claude thinks, streaming the answer so the user sees words in a second instead of waiting twenty, turning provider errors into responses a front end can handle, and keeping the code testable without spending money. Every chatbot, copilot and RAG app you build from now on sits on this pattern.

## 1. Async handlers and `AsyncAnthropic`

An LLM call spends almost all its time waiting for the network. In *Async Python* you saw that `async`/`await` lets one process wait on many things at once. FastAPI is built for this: an `async def` handler that `await`s an LLM call frees the server to handle other requests while it waits.

That only works if the client is async too. Use `anthropic.AsyncAnthropic`, never the sync `anthropic.Anthropic`, inside `async def` handlers:

```python
import anthropic
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()
client = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    response = await client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        system="You are a helpful support assistant. Be concise.",
        messages=[{"role": "user", "content": req.message}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    return ChatResponse(reply=text)
```

Notice what the backend decides, not the client: the model, the system prompt, `max_tokens`, and a 4,000-character cap on input. Those are your cost and safety controls. (For experiments, `"claude-haiku-5-5"` is far cheaper: $0.10 / $0.50 per million input/output tokens versus $4 / $20 for Opus 5.5.)

This works, but the client is a module-level global. To test `/chat` you'd have to call the real API or monkey-patch the module. There's a better way.

## 2. The client as a dependency

Make the client a dependency, exactly like the settings in *FastAPI fundamentals*:

```python
from functools import lru_cache
from typing import Annotated

from fastapi import Depends


@lru_cache
def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(timeout=60.0, max_retries=2)


Client = Annotated[anthropic.AsyncAnthropic, Depends(get_client)]


@app.post("/chat")
async def chat(req: ChatRequest, client: Client) -> ChatResponse:
    response = await client.messages.create(...)
    ...
```

- `lru_cache` means one client for the whole app. The client holds a pool of HTTP connections; creating a new one per request throws that away and is slower.
- `Client = Annotated[..., Depends(get_client)]` is a reusable alias, so every handler just writes `client: Client`.
- Now a test can replace it:

```python
app.dependency_overrides[get_client] = lambda: fake_client
```

### Testing with a fake async client

Your tests use the same `FakeAnthropic` you met in the LLM APIs section, but it's synchronous and the handler `await`s. A tiny adapter fixes that:

```python
from fake_llm import FakeAnthropic, reply, text


class AsyncFake:
    """Wrap FakeAnthropic so `await client.messages.create(...)` works."""
    def __init__(self, fake):
        self.fake = fake
        self.messages = self

    async def create(self, **kwargs):
        return self.fake.messages.create(**kwargs)


def test_chat_returns_reply():
    fake = FakeAnthropic([reply(text("Hello!"))])
    app.dependency_overrides[get_client] = lambda: AsyncFake(fake)
    r = TestClient(app).post("/chat", json={"message": "Hi"})
    assert r.json() == {"reply": "Hello!"}
    assert fake.calls[0]["messages"] == [{"role": "user", "content": "Hi"}]
    app.dependency_overrides.clear()
```

Offline, free, and the test can check exactly what you sent to the model.

## 3. Config from the environment

Hard-coding the model name, timeouts or keys means editing code to change them. Read them from the environment, with defaults, in one place:

```python
import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    model: str = "claude-opus-5-5"
    max_tokens: int = 1024
    llm_timeout: float = 60.0


@lru_cache
def get_settings() -> Settings:
    load_dotenv()  # reads .env in development; does nothing if there isn't one
    return Settings(
        model=os.environ.get("MODEL", "claude-opus-5-5"),
        max_tokens=int(os.environ.get("MAX_TOKENS", "1024")),
        llm_timeout=float(os.environ.get("LLM_TIMEOUT", "60")),
    )
```

`ANTHROPIC_API_KEY` itself doesn't need to pass through your settings: the SDK reads it from the environment. Locally it lives in a git-ignored `.env`; on a hosting platform you set it in the dashboard. Pydantic validates the types, so `MAX_TOKENS=lots` fails loudly at startup instead of mysteriously at request time.

> **Note:** The `pydantic-settings` package (`pip install pydantic-settings`) automates this: a `BaseSettings` subclass fills its fields from environment variables by name. The FastAPI docs page on settings shows it. The hand-written version above is all it does underneath.

## 4. Timeouts and error mapping

Claude can be slow, rate-limited or overloaded. Your users shouldn't see a 500 with a stack trace when that happens. Decide what each failure means for *your* client:

| What happened upstream | What you return | Why |
|---|---|---|
| 429 rate limit, 529 overloaded, other 5xx | **503 Service Unavailable** | temporary; the client should retry later |
| 400/401/403/404 from the API | **502 Bad Gateway** | your server sent a bad request or has a bad key: not the user's fault, and retrying won't help |
| no response within your timeout | **504 Gateway Timeout** | the upstream was too slow |
| a bug in your own code | 500 (let it raise) | you want to see these in logs |

The 4xx codes from the provider become 5xx codes from you, because from the user's point of view your server failed, not their request. Their request was already validated by Pydantic.

```python
from fastapi import HTTPException


def llm_error_to_http(e: Exception) -> HTTPException:
    status = getattr(e, "status_code", None)
    if status == 429 or (status is not None and status >= 500):
        return HTTPException(503, "The AI service is busy. Please try again shortly.",
                             headers={"Retry-After": "10"})
    return HTTPException(502, "The AI service rejected the request.")


@app.post("/chat")
async def chat(req: ChatRequest, client: Client) -> ChatResponse:
    try:
        response = await client.messages.create(
            model="claude-opus-5-5", max_tokens=1024,
            messages=[{"role": "user", "content": req.message}],
        )
    except anthropic.APITimeoutError:
        raise HTTPException(504, "The AI service took too long to respond.")
    except anthropic.APIStatusError as e:  # anything with an HTTP status from the API
        raise llm_error_to_http(e)
    ...
```

Some details:

- **Order matters.** `APITimeoutError` is a connection error without a status code; catch it first.
- The SDK already **retries** 429/5xx twice by default (`max_retries`), with backoff. By the time your `except` runs, retries have failed. Don't add another retry loop on top inside a request handler; users would wait too long.
- Set a **timeout** on the client: `AsyncAnthropic(timeout=60.0)`. The default is generous (up to ten minutes), which is right for batch jobs and wrong for a web request where a person is waiting.
- Branching on `status_code` (rather than only on exception classes) makes the mapping work with any client that exposes it, including the fake in tests.
- Never put the provider's raw error message in your response. It may contain request details you don't want to expose. Log it server-side instead.

## 5. Streaming to the browser

In *Streaming responses* you learned that streaming cuts the time to the first word from many seconds to under one. To get that benefit in a web app, your backend must stream too: receive chunks from Claude and forward each one to the browser immediately.

FastAPI's `StreamingResponse` takes any generator, including an async generator, and sends each yielded string as it's produced:

```python
from fastapi.responses import StreamingResponse


async def stream_text(client, message: str):
    async with client.messages.stream(
        model="claude-opus-5-5", max_tokens=4096,
        messages=[{"role": "user", "content": message}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield chunk


@app.post("/chat/plain-stream")
async def chat_plain_stream(req: ChatRequest, client: Client):
    return StreamingResponse(stream_text(client, req.message), media_type="text/plain")
```

### Server-sent events (SSE)

Plain text works, but the browser can't tell a text chunk from an error or from "done". **Server-sent events** is the standard format for a one-way stream of messages over HTTP, and it's what Anthropic's own API uses. The format is text, one event per block, each block ending in a blank line:

```
data: {"text": "Hello"}

data: {"text": " there"}

data: [DONE]

```

The rules: each event is one or more `data: ...` lines followed by an empty line (`\n\n`). Encoding each payload as JSON keeps it on one line even when the text contains newlines, because `json.dumps` turns a newline into `\n`. The media type is `text/event-stream`.

```python
import json


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def token_events(client, message: str):
    try:
        async with client.messages.stream(
            model="claude-opus-5-5", max_tokens=4096,
            messages=[{"role": "user", "content": message}],
        ) as stream:
            async for chunk in stream.text_stream:
                yield sse_event({"text": chunk})
    except Exception as e:
        if getattr(e, "status_code", None) is None:
            raise  # a bug: let it surface
        yield sse_event({"error": "The AI service failed. Please try again."})
    yield "data: [DONE]\n\n"


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, client: Client):
    return StreamingResponse(token_events(client, req.message), media_type="text/event-stream")
```

The important subtlety: **once streaming starts, the status code has already been sent.** The response went out as `200 OK` with the first byte. If Claude fails halfway, you can't change it to a 503. The only way to tell the browser is *inside* the stream, which is why `token_events` yields an `error` event and then still sends `[DONE]`. The front end checks for it.

On the browser side, reading the stream looks like this (JavaScript, for reference):

```javascript
const res = await fetch("/chat/stream", {method: "POST", headers: {"Content-Type": "application/json"},
                                         body: JSON.stringify({message: "Hi"})});
const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
// read chunks, split on "\n\n", strip "data: ", JSON.parse, append .text to the page
```

> **Note:** Recent FastAPI versions also include `fastapi.sse.EventSourceResponse`. Set `response_class=EventSourceResponse` on the route and `yield` dicts or `ServerSentEvent` objects; it formats the events, adds keep-alive pings and sets no-cache headers for you. Writing the format by hand once, as above, is the best way to understand what it does.

### Testing a streaming endpoint

`TestClient` collects the whole streamed body, so tests can parse it:

```python
r = client.post("/chat/stream", json={"message": "Hi"})
assert r.headers["content-type"].startswith("text/event-stream")
events = [block.removeprefix("data: ") for block in r.text.split("\n\n") if block]
# ['{"text": "Hello "}', '{"text": "there"}', '[DONE]']
```

For the fake, the async adapter needs a `stream()` method that returns an async context manager whose `text_stream` is an async iterator. The exercise tests include one: read it, it's ten lines.

> **Try it:** In the streaming exercise, Run the starter with a key set and watch the raw SSE lines print one by one.

## 6. Putting it together

A production-shaped `main.py` for this lesson's pieces, in order: settings from the environment, a cached client dependency built from those settings, Pydantic request/response models, a non-streaming `/chat` with error mapping, and a streaming `/chat/stream` that reports errors in-band. Add the API-key dependency from *FastAPI fundamentals* to both routes and you have a backend you could put in front of a real website. The section project builds exactly this, plus retrieval.

## Common mistakes

- **Using the sync `Anthropic` client in an `async def` handler.** Every request blocks the whole server while Claude thinks. Use `AsyncAnthropic`.
- **Creating a new client per request.** You lose connection reuse. Build it once (a cached dependency).
- **Letting provider errors escape as 500s.** Map them: 503 for temporary, 502 for "we sent something bad", 504 for timeouts.
- **Echoing the provider's error text to users.** Log it; return a generic message.
- **Expecting to change the status code mid-stream.** You can't; send an error event inside the stream.
- **Forgetting the blank line in SSE.** `data: x\n` without the second `\n` isn't a complete event, and the browser waits forever.
- **No timeout.** A request with no timeout can hang for minutes and tie up a worker.

## Recap

- `async def` handlers plus `AsyncAnthropic` let one server handle many slow LLM calls at once.
- Provide the client through a cached dependency (`Depends(get_client)`), so tests swap it with `app.dependency_overrides`.
- Read model, limits and timeouts from the environment into a validated `Settings`.
- Map upstream failures: 429/5xx → 503, other 4xx → 502, timeout → 504; never leak raw provider errors.
- `StreamingResponse` with an async generator streams Claude's chunks; SSE (`data: {...}\n\n`, `text/event-stream`) gives the browser structured events.
- Errors after streaming has started must be reported inside the stream.
