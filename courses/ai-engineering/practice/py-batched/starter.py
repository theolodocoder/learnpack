from collections.abc import Iterable, Iterator
from itertools import count, islice


def batched[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield lists of `size` items from `items`; the last one may be shorter."""
    # TODO: raise ValueError right away if size < 1
    # TODO: define an inner generator that loops and yields batches, and return it
    raise NotImplementedError


if __name__ == "__main__":
    try:
        print(list(batched([1, 2, 3, 4, 5], 2)))
        first_two = list(islice(batched(count(), 3), 2))  # count() never ends
        print(first_two)
    except NotImplementedError:
        print("Not implemented yet: fill in the TODOs, then Run again.")
