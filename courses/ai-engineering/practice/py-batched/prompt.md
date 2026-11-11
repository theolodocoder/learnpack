# Batch items lazily

Embedding APIs and bulk LLM jobs take inputs in batches: 100 documents per request, not 100,000 at once. Write a generator that groups any iterable into lists of a fixed size.

```python
def batched(items: Iterable[T], size: int) -> Iterator[list[T]]:
```

- Yield lists of `size` items, in order. The last list may be shorter.
- Yield nothing for an empty iterable.
- Raise `ValueError` if `size < 1`. Raise it **when `batched` is called**, not later when someone starts looping. (Hint: a function that contains `yield` doesn't run at all until the first `next()`. Do the check in `batched` and put the `yield` loop in an inner generator function that you return.)
- Be lazy: it must work on an infinite iterator, pulling only the items it needs.

Example:

```python
list(batched([1, 2, 3, 4, 5], 2))   # [[1, 2], [3, 4], [5]]
```

> **Note:** Python 3.12 added `itertools.batched`, which yields tuples. Write your own here (you may use `itertools.islice` inside it).
