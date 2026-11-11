# Decorators and context managers

## Why this matters

Production AI code needs the same extras around many different calls: retry when the API is overloaded, time how long each step takes, log inputs and outputs, cache expensive results, and always close connections. Decorators let you add that behaviour to any function with one line (`@retry(times=3)`), and context managers guarantee setup and cleanup around a block (`with client:`). You'll also see both all over the libraries you'll use: FastAPI routes are decorators, and SDK clients and streams are context managers.

## Functions are values

In Python, a function is an object like any other. You can store it in a variable, put it in a dict, pass it to another function, or return it from one.

```python
def shout(text: str) -> str:
    return text.upper() + "!"

say = shout                     # no parentheses: the function itself, not a call
print(say("hi"))                # HI!

handlers = {"shout": shout, "quiet": str.lower}
print(handlers["quiet"]("HeLLo"))   # hello

def apply_twice(f, x):
    return f(f(x))

print(apply_twice(lambda n: n * 3, 2))   # 18
```

`lambda args: expression` creates a small unnamed function. Use it for short throwaway functions like sort keys: `sorted(docs, key=lambda d: d["score"], reverse=True)`.

Passing functions around is everywhere in AI code. A tool registry for an agent is often just a dict from tool name to Python function.

## Closures

A function defined inside another function can use the outer function's variables, even after the outer function has returned. That combination (inner function plus the variables it remembers) is a **closure**.

```python
def make_prefixer(prefix: str):
    def add_prefix(text: str) -> str:
        return f"{prefix}{text}"      # uses `prefix` from the enclosing call
    return add_prefix

warn = make_prefixer("[WARN] ")
info = make_prefixer("[INFO] ")
print(warn("disk almost full"))   # [WARN] disk almost full
print(info("started"))            # [INFO] started
```

Each call to `make_prefixer` creates a new inner function with its own remembered `prefix`. To **reassign** an outer variable (not just read it) from the inner function, declare it `nonlocal`:

```python
def make_counter():
    count = 0
    def increment() -> int:
        nonlocal count
        count += 1
        return count
    return increment

c = make_counter()
print(c(), c(), c())   # 1 2 3
```

## Decorators

A **decorator** is a function that takes a function and returns a new function, usually one that wraps the original with extra behaviour. The `@` syntax is shorthand:

```python
@my_decorator
def f(): ...

# means exactly:
def f(): ...
f = my_decorator(f)
```

Here's a decorator that logs every call:

```python
import functools

def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"calling {func.__name__} with {args} {kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result!r}")
        return result
    return wrapper

@log_calls
def add(a, b):
    """Add two numbers."""
    return a + b

add(2, b=3)
# calling add with (2,) {'b': 3}
# add returned 5
```

The pieces:

- `wrapper(*args, **kwargs)` accepts any arguments and passes them through unchanged, so the decorator works on any function.
- `wrapper` is a closure: it remembers `func`.
- `return result` matters. Forgetting it makes every decorated function return `None`.
- `@functools.wraps(func)` copies the original's `__name__`, docstring and other metadata onto `wrapper`. Without it, `add.__name__` would be `"wrapper"`, which breaks logging, debugging, and frameworks that look at function names (FastAPI and pytest both do).

### Decorators with arguments

`@retry(times=3)` has parentheses, so `retry(times=3)` is called first, and **its result** is the decorator. That means three levels of functions: the outer one takes the options, returns a decorator, which returns the wrapper.

```python
import functools

def repeat(n: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(n)]
        return wrapper
    return decorator

@repeat(3)
def roll():
    import random
    return random.randint(1, 6)

print(roll())   # e.g. [4, 1, 6]
```

### A retry decorator with backoff

Network calls to LLM APIs fail regularly with temporary errors: 429 (rate limited), 529 (overloaded), 5xx server errors and dropped connections. The standard fix is **retry with exponential backoff**: wait a little, try again, and double the wait each time, so a struggling server gets breathing room.

```python
import functools
import time

def retry(times: int = 3, base_delay: float = 0.5, retry_on=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except retry_on as err:
                    if attempt == times - 1:
                        raise                      # out of attempts: re-raise the last error
                    delay = base_delay * 2 ** attempt
                    print(f"{func.__name__} failed ({err!r}); retrying in {delay}s")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(times=4, base_delay=0.1, retry_on=(ConnectionError, TimeoutError))
def call_api():
    ...
```

Delays go 0.1, 0.2, 0.4 seconds between the four attempts. Points worth noticing:

- **Retry only errors that can succeed later.** A 400 Bad Request (your request is wrong) will fail every time; retrying just wastes money. That's what `retry_on` is for. With API errors that carry a `status_code`, you'd retry on 429 and 5xx only.
- **A bare `raise`** re-raises the exception being handled, with its original traceback.
- Real-world versions add **jitter** (a random extra delay) so many clients don't retry in lockstep, and a cap on the maximum delay. Libraries like `tenacity` provide all this, and the Claude SDK already retries twice by default (`max_retries`). Writing your own once teaches you what those settings mean.

> **Try it:** In the exercise, `retry` takes a `sleep` parameter defaulting to `time.sleep`. Tests pass a fake that records the delays instead of waiting. Making a dependency a parameter like this is the simplest way to make code testable.

## Context managers

A **context manager** sets something up, runs a block of code, and then cleans up, even if the block raises. You use one with `with`:

```python
from pathlib import Path

with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("hello")
# the file is closed here, no matter what happened inside
```

Behind the scenes, `with` calls the object's `__enter__` method at the start (its return value is what `as` binds) and `__exit__` at the end. `__exit__` runs on normal exit **and** when an exception escapes the block, which is what makes cleanup reliable. It's equivalent to a `try`/`finally`, but packaged so you can't forget it.

Things you'll manage with `with` in this course: files, HTTP clients (`with httpx.Client() as client:`), streaming responses (`with client.messages.stream(...) as stream:`), database connections and transactions, and locks.

### Writing one with `contextlib.contextmanager`

The easiest way to write your own is a generator with exactly one `yield`, decorated with `@contextmanager`. Code before the `yield` is the setup, the yielded value is what `as` receives, and code after is the cleanup. Wrap the `yield` in `try`/`finally` so cleanup runs even on errors:

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")

with timer("embedding batch"):
    time.sleep(0.1)
# embedding batch: 0.100s
```

`time.perf_counter()` is the right clock for measuring durations: high resolution and never jumps backwards (unlike `time.time()`, which follows the wall clock).

If the block raises, the exception is re-raised at the `yield`, `finally` runs, and the exception continues to propagate. That's what you want for a timer: record the time, don't hide the error.

To give the block something to use, yield a value. A common trick for timers is to yield a dict and fill it in afterwards:

```python
@contextmanager
def timed(label: str):
    result = {"label": label, "seconds": None}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["seconds"] = time.perf_counter() - start

with timed("model call") as t:
    time.sleep(0.05)
print(t)   # {'label': 'model call', 'seconds': 0.05...}
```

### Writing one as a class

For objects that hold a resource, implementing `__enter__` and `__exit__` directly is common. This is how SDK clients work:

```python
class Connection:
    def __enter__(self):
        print("open")
        return self                       # what `as` gets
    def __exit__(self, exc_type, exc, tb):
        print("close")
        return False                      # False: don't swallow exceptions

with Connection() as conn:
    print("using", conn)
# open / using <__main__.Connection ...> / close
```

`__exit__` receives the exception (or `None`s if there wasn't one). Returning `True` would suppress the exception, which you almost never want.

## Where you'll see these in AI code

- **FastAPI** registers routes with decorators that take arguments, exactly the three-level pattern above:

  ```python
  @app.post("/chat")
  async def chat(request: ChatRequest) -> ChatResponse: ...
  ```

- **SDK clients and streams** are context managers so connections and streams are always closed:

  ```python
  with client.messages.stream(model=..., max_tokens=..., messages=...) as stream:
      for chunk in stream.text_stream: ...
  ```

- **`functools.lru_cache`** is a standard-library decorator that remembers results for repeated arguments, useful for caching embeddings of the same text within a run.
- **Tracing and evaluation tools** (which you'll use later for observability) commonly offer a decorator you put on a function to record each call's inputs, outputs and timing.

## Common mistakes

- **Forgetting `return` in the wrapper.** Every decorated function then returns `None`.
- **Forgetting `functools.wraps`.** The function loses its name and docstring; frameworks and logs get confused.
- **Mixing up `@deco` and `@deco()`.** A decorator with arguments must be called; `@retry` without parentheses passes your function as `times`.
- **Retrying everything.** Retrying a 400 or a bug just repeats the failure, slower. Limit `retry_on`.
- **Cleanup outside `finally`.** In a `@contextmanager`, code after a bare `yield` is skipped when the block raises.
- **Swallowing exceptions in `__exit__`** by returning `True`, or catching and not re-raising in a `@contextmanager`.

## Recap

- Functions are values: pass them, store them, return them. Closures remember variables from the enclosing call.
- A decorator takes a function and returns a wrapper; `@deco` is `f = deco(f)`. Use `*args, **kwargs`, return the result, and apply `functools.wraps`.
- Decorators with arguments add a third layer: `retry(times=3)` returns the decorator.
- Retry with exponential backoff (`base_delay * 2 ** attempt`) only on temporary errors, and re-raise when out of attempts.
- Context managers guarantee cleanup: `@contextmanager` with `try: yield ... finally:`, or a class with `__enter__`/`__exit__`.
