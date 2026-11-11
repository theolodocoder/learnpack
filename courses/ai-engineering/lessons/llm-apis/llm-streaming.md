# Streaming responses

## Why this matters

A long answer can take 20–60 seconds to generate. Without streaming, your user stares at a spinner for all of it and then gets a wall of text at once. With streaming, the first words appear within a second or two, and the answer types itself out as the model writes it. That's the difference between an app that feels broken and one that feels fast, even though the total time is the same. Streaming also keeps long-running requests healthy: a connection that receives data continuously is far less likely to be cut by a timeout than one that sits silent for minutes.

## 1. What streaming actually is

Remember from the first lesson that the model generates one token at a time. A normal `messages.create` call waits until the last token is done and then returns everything. A **streaming** call sends each piece as soon as it exists.

Under the hood the API uses **server-sent events** (SSE): one long HTTP response that delivers a series of small events: "message started", "here's some text", "here's some more text", …, "message finished, here's the final usage". The SDK parses these for you, so you mostly deal with plain strings.

Two numbers describe the user experience:

- **Time to first token**: how long until something appears. Streaming makes this short.
- **Total time**: how long until the answer is complete. Streaming doesn't change this.

## 2. `messages.stream` and `text_stream`

The SDK's streaming helper is a context manager:

```python
import anthropic

client = anthropic.Anthropic()

with client.messages.stream(
    model="claude-opus-5-5",
    max_tokens=64000,
    messages=[{"role": "user", "content": "Explain HTTP caching to a junior developer."}],
) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="", flush=True)
    print()
    final = stream.get_final_message()

print(final.stop_reason, final.usage.output_tokens)
```

Line by line:

- `client.messages.stream(...)` takes **exactly the same arguments** as `messages.create`: `model`, `max_tokens`, `system`, `messages`, `tools`, and so on.
- The `with` block opens the HTTP connection and guarantees it's closed afterwards, even if your code raises an exception halfway through.
- `stream.text_stream` is an iterator of **strings**: just the text pieces, with all the event plumbing hidden. Each chunk might be a word, part of a word, or a few words.
- `print(chunk, end="", flush=True)` prints without a newline and forces the terminal to show it immediately (otherwise Python may buffer output and you lose the effect).
- `stream.get_final_message()` waits for the stream to finish and returns the complete `Message`, the same object `messages.create` would have returned, with `.content`, `.stop_reason` and `.usage`. Call it **inside** the `with` block.

> **Note:** Notice `max_tokens=64000` here versus `16000` in non-streamed examples. When you allow very long outputs, stream. The SDK refuses a non-streaming request whose `max_tokens` is large enough that it might run for more than ten minutes, and tells you to use streaming instead.

### Collecting the full text

Often you want to show the text live **and** keep it:

```python
chunks: list[str] = []
with client.messages.stream(model="claude-haiku-5-5", max_tokens=4000,
                            messages=[{"role": "user", "content": "Name three Nigerian dishes."}]) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="", flush=True)
        chunks.append(chunk)
    print()
    final = stream.get_final_message()

full_text = "".join(chunks)
```

Joining a list once at the end is faster than `full_text += chunk` in the loop, and it gives you the individual chunks if you want them (for timing, or to test your code).

Since the final message contains the full content too, you can also skip collecting and read it at the end:

```python
answer = "".join(b.text for b in final.content if b.type == "text")
```

## 3. Streaming is a generator problem

You already know generators from the Python refresher: functions that `yield` values one at a time, lazily, as the caller asks for them. `text_stream` *is* an iterator, and the cleanest way to expose streaming from your own code is to wrap it in a generator function:

```python
from collections.abc import Iterator


def stream_answer(client, question: str, model: str = "claude-opus-5-5") -> Iterator[str]:
    with client.messages.stream(
        model=model, max_tokens=16000,
        messages=[{"role": "user", "content": question}],
    ) as stream:
        yield from stream.text_stream
```

`yield from` re-yields every item of the inner iterator. Now callers decide what to do with each chunk, and your function doesn't care whether it's going to a terminal, a web page or a test:

```python
for piece in stream_answer(client, "What is a vector database?"):
    print(piece, end="", flush=True)
```

Some useful properties, all coming from generator semantics:

- **Lazy.** Calling `stream_answer(...)` doesn't contact the API. The request starts on the first `next()` (the first loop iteration). This catches people out in tests: if you never iterate, nothing happens.
- **Clean-up still works.** The `with` block lives inside the generator. When the loop finishes, or the caller stops early with `break`, Python closes the generator, the `with` block exits, and the connection is released.
- **Composable.** You can chain generators: one that streams, one that filters, one that counts tokens per second.

```python
import time

def with_timing(chunks):
    start = time.perf_counter()
    first = None
    for c in chunks:
        if first is None:
            first = time.perf_counter() - start
            print(f"[first token after {first:.2f}s]")
        yield c

for piece in with_timing(stream_answer(client, "Tell me a short story.")):
    print(piece, end="", flush=True)
```

> **Try it:** Run the timing example once with `stream_answer` and once with a plain `messages.create` call. Compare the time to first visible text.

### Where this goes next: web APIs

In the backend section you'll serve LLM answers from FastAPI. Its `StreamingResponse` accepts exactly this kind of generator, so the same `stream_answer` function streams straight to a browser. A preview:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/ask")
def ask(q: str):
    return StreamingResponse(stream_answer(client, q), media_type="text/plain")
```

## 4. Async streaming

In async code (FastAPI handlers, batch jobs), use `AsyncAnthropic`. The shape is identical, with `async with` and `async for`:

```python
import asyncio
import anthropic

client = anthropic.AsyncAnthropic()


async def main() -> None:
    async with client.messages.stream(
        model="claude-haiku-5-5", max_tokens=4000,
        messages=[{"role": "user", "content": "Count to ten in Igbo."}],
    ) as stream:
        async for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
        print()
        final = await stream.get_final_message()
    print(final.usage.output_tokens)


asyncio.run(main())
```

The async version of a streaming generator is an **async generator**: an `async def` function containing `yield`, iterated with `async for`.

```python
async def stream_answer_async(client, question: str):
    async with client.messages.stream(
        model="claude-opus-5-5", max_tokens=16000,
        messages=[{"role": "user", "content": question}],
    ) as stream:
        async for chunk in stream.text_stream:
            yield chunk
```

## 5. Beyond text: events

`text_stream` hides everything except text. If you need more, iterate the stream itself to get typed events:

```python
with client.messages.stream(model="claude-haiku-5-5", max_tokens=2000,
                            messages=[{"role": "user", "content": "Hi!"}]) as stream:
    for event in stream:
        if event.type == "text":
            print(event.text, end="", flush=True)
        elif event.type == "message_stop":
            print("\n[done]")
```

You'll rarely need this for chat. It matters when streaming tool calls, where the tool's input JSON arrives in pieces; for most tool-using code it's simpler to call `get_final_message()` and work with complete blocks.

## 6. When not to stream

Streaming adds code paths and makes error handling slightly trickier (an error can arrive halfway through, after you've shown half an answer). Skip it when:

- **No human is watching**: batch extraction, background jobs, classification. Use `messages.create` (unless outputs are very long).
- **You need the whole output before doing anything**: parsing JSON, for example. Partial JSON is useless, so stream only if the output is long enough to risk a timeout, and parse `get_final_message()` at the end.

Stream when a person is waiting on the text, or when outputs are long.

## Common mistakes

- **Forgetting `flush=True`**, so the terminal buffers output and the "typing" effect disappears.
- **Calling `get_final_message()` outside the `with` block.** The stream has been closed by then. Call it inside.
- **Using `+=` on a string in a hot loop.** Collect chunks in a list and `"".join()` once.
- **Expecting a generator to run when called.** It runs when iterated. A test that calls `stream_answer(...)` but never loops checks nothing.
- **Trying to parse JSON from partial chunks.** Wait for the final message.
- **Showing a half answer after an error with no explanation.** If the stream fails midway, tell the user the answer is incomplete.

## Recap

- Streaming cuts the time to first token, not the total time, and keeps long requests alive.
- `with client.messages.stream(...) as stream:` takes the same arguments as `create`.
- `stream.text_stream` yields text chunks; `stream.get_final_message()` gives the complete `Message` with `usage` and `stop_reason`.
- Wrap streaming in a generator (`yield from stream.text_stream`) so callers decide where chunks go. Generators are lazy: nothing happens until you iterate.
- Async code uses `AsyncAnthropic`, `async with` and `async for`.
- Stream for humans and long outputs; use plain `create` for short background work.
