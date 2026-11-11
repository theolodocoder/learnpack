# An LRU cache with `OrderedDict`

A classic live-coding question, and a useful one: you'd put a cache like this in front of an embedding call so repeated questions don't cost money twice.

An **LRU** (least recently used) cache holds at most `capacity` items. When it's full and a new key arrives, it evicts the item that was used **longest ago**. Both reading a key and writing it count as "using" it.

Write:

```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key, default=None): ...
    def put(self, key, value) -> None: ...
    def __len__(self) -> int: ...
```

1. `__init__` raises `ValueError` if `capacity` is less than 1.
2. `get(key, default=None)` returns the stored value and marks the key as most recently used. If the key is missing, return `default`.
3. `put(key, value)` stores the value and marks the key as most recently used. If the key already exists, update its value (this does not grow the cache). If adding a new key makes the cache exceed `capacity`, evict the least recently used key.
4. `len(cache)` returns the number of items stored.

Use `collections.OrderedDict`: `move_to_end(key)` marks a key as most recent, and `popitem(last=False)` removes the oldest. Both are O(1).

## Example

```python
cache = LRUCache(2)
cache.put("a", 1)
cache.put("b", 2)
cache.get("a")        # 1   ("a" is now most recent)
cache.put("c", 3)     # cache is full: evicts "b", the least recently used
cache.get("b")        # None
cache.get("c")        # 3
len(cache)            # 2
```

In an interview, mention that `functools.lru_cache` exists for caching function results, and that you're building it by hand because the question asks how it works.
