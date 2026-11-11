# A timer context manager

Latency matters in AI apps: you'll want to know how long each model call, retrieval step or tool run takes. Write a context manager that times its block.

```python
@contextmanager
def timer(label: str, log: list[dict] | None = None) -> Iterator[dict]:
```

- On entry, yield a dict `{"label": label, "seconds": None}`.
- When the block ends, set `"seconds"` to the elapsed time (use `time.perf_counter()`), and if `log` is given, append the dict to it.
- This must happen **even if the block raises**, and the exception must still propagate (don't swallow it). A `try` / `finally` around the `yield` does this.

Example:

```python
log = []
with timer("call model", log) as t:
    time.sleep(0.05)
print(t)    # {'label': 'call model', 'seconds': 0.0502...}
print(log)  # [the same dict]
```
