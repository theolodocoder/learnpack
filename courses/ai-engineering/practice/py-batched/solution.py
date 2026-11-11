from collections.abc import Iterable, Iterator
from itertools import count, islice


def batched[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield lists of `size` items from `items`; the last one may be shorter."""
    if size < 1:
        raise ValueError("size must be at least 1")

    def gen() -> Iterator[list[T]]:
        it = iter(items)
        while batch := list(islice(it, size)):
            yield batch

    return gen()


if __name__ == "__main__":
    print(list(batched([1, 2, 3, 4, 5], 2)))
    first_two = list(islice(batched(count(), 3), 2))  # count() never ends
    print(first_two)
