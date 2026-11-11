# Async Python

## Why this matters

An LLM call takes seconds, and almost all of that time your program is just waiting for the network. If you need to classify 500 support tickets, doing them one after another at 3 seconds each takes 25 minutes. Running 20 at a time takes about 75 seconds. `asyncio` lets one Python process wait on many network calls at once, and it's how FastAPI serves many users concurrently, how agents call several tools in parallel, and how you'll run evaluation suites in reasonable time.

## Why async: I/O-bound work

Programs spend time in two ways:

- **CPU-bound:** actually computing (resizing images, training a model, crunching numbers). The CPU is busy.
- **I/O-bound:** waiting for something outside: a network response, a disk, a database. The CPU is idle.

LLM and HTTP calls are I/O-bound. Async doesn't make any single call faster; it lets your program do something useful (start other calls) **while** waiting. It runs everything in one thread: an **event loop** switches between tasks at the points where they wait.

> **Note:** Async does not help CPU-bound work. A heavy computation inside async code blocks everything. For CPU-heavy work, use processes (`concurrent.futures.ProcessPoolExecutor`) or libraries that release the GIL, like numpy.

## `async def` and `await`

`async def` defines a **coroutine function**. Calling it doesn't run the body; it returns a **coroutine object**, a paused piece of work. `await` runs a coroutine (or other awaitable) and waits for its result, letting the event loop run other tasks in the meantime.

```python
import asyncio

async def fetch_answer(question: str) -> str:
    await asyncio.sleep(1)          # stands in for a network call
    return f"answer to {question!r}"

async def main():
    answer = await fetch_answer("What is RAG?")
    print(answer)

asyncio.run(main())
```

- `asyncio.run(main())` starts the event loop, runs `main()` to completion, and shuts the loop down. Call it **once**, at the top of your program.
- `await` can only be used inside an `async def`.
- `asyncio.sleep` is the async version of `time.sleep`: it pauses this task without blocking others.

If you call a coroutine function and forget `await`, you get a coroutine object instead of a result, plus a `RuntimeWarning: coroutine ... was never awaited`. When you see that warning, look for the missing `await`.

## Running things concurrently: `asyncio.gather`

`await` one call after another and they still run in sequence:

```python
import asyncio, time

async def fetch(n: int) -> int:
    await asyncio.sleep(1)
    return n * 10

async def sequential():
    return [await fetch(1), await fetch(2), await fetch(3)]   # about 3 s

async def concurrent():
    return await asyncio.gather(fetch(1), fetch(2), fetch(3))  # about 1 s

start = time.perf_counter()
print(asyncio.run(concurrent()), f"{time.perf_counter() - start:.1f}s")
# [10, 20, 30] 1.0s
```

`asyncio.gather(*aws)` starts all the awaitables together and waits for all of them. It returns the results **in the order you passed them**, regardless of which finished first. With a list, unpack it: `await asyncio.gather(*(fetch(n) for n in range(100)))`.

By default, if one awaitable raises, `gather` raises that exception (the others keep running in the background, and their results are lost to you). Pass `return_exceptions=True` to get exceptions back as values in the result list instead:

```python
async def might_fail(n):
    await asyncio.sleep(0.1)
    if n == 2:
        raise ValueError("bad item")
    return n

async def main():
    results = await asyncio.gather(*(might_fail(n) for n in range(4)), return_exceptions=True)
    for r in results:
        print("error:" if isinstance(r, Exception) else "ok:", r)

asyncio.run(main())
# ok: 0 / ok: 1 / error: bad item / ok: 3
```

For batch jobs over many items, that's usually what you want: one bad item shouldn't lose the other 499 results.

### Tasks and TaskGroup

`asyncio.create_task(coro)` schedules a coroutine to start running right away in the background and returns a `Task` you can await later. Python 3.11 added `asyncio.TaskGroup`, which starts tasks and waits for all of them when the `async with` block ends; if one fails, it cancels the rest:

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch(1))
        t2 = tg.create_task(fetch(2))
    print(t1.result(), t2.result())    # 10 20
```

Use `gather` when you want a list of results in order (optionally with errors as values), `TaskGroup` when any failure should cancel everything.

## Limiting concurrency: `asyncio.Semaphore`

Starting 500 LLM requests at once is a bad idea. You'll hit rate limits (429 errors), the provider may throttle you, and you may run out of connections. You want "as many as possible, but no more than N at a time". A **semaphore** is a counter of permits: `async with sem:` takes a permit (waiting if none are free) and gives it back at the end of the block.

```python
import asyncio

async def classify(ticket: str) -> str:
    await asyncio.sleep(0.5)            # pretend LLM call
    return f"{ticket}: billing"

async def classify_all(tickets: list[str], limit: int = 5) -> list[str]:
    sem = asyncio.Semaphore(limit)

    async def one(ticket: str) -> str:
        async with sem:                  # at most `limit` tasks get past this line at once
            return await classify(ticket)

    return await asyncio.gather(*(one(t) for t in tickets))

results = asyncio.run(classify_all([f"ticket-{i}" for i in range(20)], limit=5))
print(len(results))   # 20, in about 2 s (4 waves of 5)
```

This "semaphore plus gather" pattern is the one you'll reuse most. All 20 tasks are created at once, but only 5 at a time get past `async with sem`. The others wait for a free permit. Results still come back in input order.

> **Try it:** Change `limit` to 1, then 20, and time it. With 1 it's sequential (about 10 s); with 20 it's about 0.5 s.

## Timeouts

A request that never answers will hang your program forever unless you set a limit. `asyncio.timeout` (3.11+) cancels the block if it takes too long and raises the built-in `TimeoutError`:

```python
import asyncio

async def slow_call():
    await asyncio.sleep(10)
    return "done"

async def main():
    try:
        async with asyncio.timeout(2):
            result = await slow_call()
    except TimeoutError:
        result = None
        print("gave up after 2 s")
    return result

asyncio.run(main())
```

`asyncio.wait_for(aw, timeout=2)` does the same for a single awaitable. HTTP clients like httpx also have their own timeout settings, which you'll see in the next lesson; use both: the client timeout for each request, and `asyncio.timeout` for an overall deadline on a group of work.

Combining timeouts and error handling per item gives a robust fan-out:

```python
async def settle(aw, seconds):
    try:
        async with asyncio.timeout(seconds):
            return ("ok", await aw)
    except TimeoutError:
        return ("timeout", None)
    except Exception as e:
        return ("error", str(e))
```

Wrap each call in `settle(...)`, gather them all, and every item reports what happened without one failure affecting the others.

## The big mistake: blocking calls inside async code

The event loop can only switch tasks at an `await`. If a coroutine calls something that blocks (waits without `await`), **every** task is frozen until it returns.

```python
import asyncio, time

async def bad():
    time.sleep(1)               # blocks the whole event loop for 1 s
    return 1

async def good():
    await asyncio.sleep(1)      # yields to the loop while waiting
    return 1

async def main():
    t = time.perf_counter()
    await asyncio.gather(*(bad() for _ in range(3)))
    print(f"bad:  {time.perf_counter() - t:.1f}s")     # bad:  3.0s
    t = time.perf_counter()
    await asyncio.gather(*(good() for _ in range(3)))
    print(f"good: {time.perf_counter() - t:.1f}s")     # good: 1.0s

asyncio.run(main())
```

Common blocking culprits:

- `time.sleep` → use `await asyncio.sleep`.
- `requests.get` or a sync `httpx.Client` → use `httpx.AsyncClient` and `await client.get(...)`.
- The sync Claude client `anthropic.Anthropic()` → use `anthropic.AsyncAnthropic()` and `await client.messages.create(...)`.
- Slow file or CPU work → move it off the loop with `await asyncio.to_thread(func, *args)`, which runs a sync function in a worker thread.

```python
import asyncio, time

def legacy_blocking_call(x):
    time.sleep(1)       # some sync library you can't change
    return x * 2

async def main():
    results = await asyncio.gather(*(asyncio.to_thread(legacy_blocking_call, i) for i in range(3)))
    print(results)      # [0, 2, 4] in about 1 s

asyncio.run(main())
```

The rule: inside `async def`, anything that waits must be awaited. If it can't be awaited, run it with `asyncio.to_thread`.

## Async with the Claude SDK

The SDK has an async client with the same methods:

```python
import asyncio
import anthropic

async def ask(client: anthropic.AsyncAnthropic, question: str) -> str:
    response = await client.messages.create(
        model="claude-haiku-5-5", max_tokens=1000,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text

async def main():
    client = anthropic.AsyncAnthropic()
    questions = ["What is a vector?", "What is a token?", "What is RAG?"]
    answers = await asyncio.gather(*(ask(client, q) for q in questions))
    for q, a in zip(questions, answers):
        print(q, "->", a[:80])

# asyncio.run(main())   # needs ANTHROPIC_API_KEY; Haiku keeps experiments cheap
```

Create one client and share it across tasks; it manages a pool of connections for you.

## Common mistakes

- **Forgetting `await`.** You get a coroutine object and a "never awaited" warning instead of a result.
- **Awaiting in a loop when you meant concurrency.** `for x in xs: await f(x)` is sequential. Use `gather` (with a semaphore).
- **Blocking calls inside `async def`.** `time.sleep`, `requests`, sync SDK clients and heavy CPU work freeze every task.
- **Unlimited concurrency.** Gathering 1,000 API calls at once triggers rate limits. Use a semaphore.
- **No timeouts.** One hung request can stall a whole batch forever.
- **Calling `asyncio.run` inside async code.** It's for the top level only; inside a coroutine, just `await`.
- **Losing results to one failure.** Use `return_exceptions=True` or per-item `try`/`except` for batch jobs.

## Recap

- Async helps I/O-bound work (network calls) by overlapping the waiting; it doesn't speed up CPU work.
- `async def` makes a coroutine; `await` runs it; `asyncio.run(main())` starts everything once.
- `asyncio.gather(*aws)` runs awaitables concurrently and returns results in input order; `return_exceptions=True` keeps going past failures.
- `asyncio.Semaphore(n)` with `async with sem:` caps how many run at once.
- `asyncio.timeout(seconds)` raises `TimeoutError` if a block takes too long.
- Never block the event loop: await async versions, or use `asyncio.to_thread` for sync code.
