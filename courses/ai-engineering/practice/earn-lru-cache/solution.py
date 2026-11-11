from collections import OrderedDict


class LRUCache:
    """A fixed-size cache that evicts the least recently used key."""

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError(f"capacity must be at least 1, got {capacity}")
        self.capacity = capacity
        self._items: OrderedDict = OrderedDict()

    def get(self, key, default=None):
        if key not in self._items:
            return default
        self._items.move_to_end(key)
        return self._items[key]

    def put(self, key, value) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        if len(self._items) > self.capacity:
            self._items.popitem(last=False)

    def __len__(self) -> int:
        return len(self._items)


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    print(cache.get("a"))  # 1
    cache.put("c", 3)      # evicts "b"
    print(cache.get("b"))  # None
    print(cache.get("c"))  # 3
    print(len(cache))      # 2
