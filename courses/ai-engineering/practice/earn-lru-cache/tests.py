from solution import LRUCache


def test_get_returns_stored_value():
    cache = LRUCache(2)
    cache.put("a", 1)
    got = cache.get("a")
    assert got == 1, f"expected 1, got {got!r}"


def test_missing_key_returns_default():
    cache = LRUCache(2)
    assert cache.get("nope") is None, f"expected None, got {cache.get('nope')!r}"
    got = cache.get("nope", "fallback")
    assert got == "fallback", f"expected 'fallback', got {got!r}"


def test_evicts_least_recently_used_when_full():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.get("a") is None, "expected 'a' (the oldest) to be evicted"
    assert cache.get("b") == 2 and cache.get("c") == 3, "expected 'b' and 'c' to still be cached"
    assert len(cache) == 2, f"expected len 2, got {len(cache)}"


def test_get_marks_key_as_recently_used():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert cache.get("b") is None, "reading 'a' should make 'b' the least recently used, so 'b' is evicted"
    assert cache.get("a") == 1, "expected 'a' to survive because it was just read"


def test_updating_a_key_does_not_grow_and_refreshes_it():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    assert len(cache) == 2, f"updating an existing key should not grow the cache; len is {len(cache)}"
    cache.put("c", 3)
    assert cache.get("a") == 10, "expected 'a' to be updated to 10 and kept (it was just written)"
    assert cache.get("b") is None, "expected 'b' to be evicted as the least recently used"


def test_rejects_capacity_below_one():
    for bad in (0, -3):
        try:
            LRUCache(bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for capacity {bad}")
