from collections import OrderedDict


class LRUCache:
    """A fixed-size cache that evicts the least recently used key."""

    def __init__(self, capacity: int):
        # TODO: raise ValueError if capacity < 1
        # TODO: store capacity and an OrderedDict for the items
        pass

    def get(self, key, default=None):
        # TODO: if key is missing, return default
        # TODO: otherwise mark it most recently used and return its value
        pass

    def put(self, key, value) -> None:
        # TODO: store the value and mark the key most recently used
        # TODO: if over capacity, evict the least recently used key
        pass

    def __len__(self) -> int:
        # TODO: return how many items are stored
        return 0


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    print(cache.get("a"))  # 1
    cache.put("c", 3)      # evicts "b"
    print(cache.get("b"))  # None
    print(cache.get("c"))  # 3
    print(len(cache))      # 2
