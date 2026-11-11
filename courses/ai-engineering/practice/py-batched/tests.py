from itertools import count, islice

from solution import batched


def test_splits_into_even_batches():
    got = list(batched([1, 2, 3, 4], 2))
    want = [[1, 2], [3, 4]]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_last_batch_can_be_shorter():
    got = list(batched("abcde", 2))
    want = [["a", "b"], ["c", "d"], ["e"]]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_empty_input_yields_nothing():
    got = list(batched([], 3))
    assert got == [], f"expected [], got {got!r}"


def test_is_lazy_on_an_infinite_iterator():
    got = list(islice(batched(count(), 3), 2))
    want = [[0, 1, 2], [3, 4, 5]]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_bad_size_raises_value_error_immediately():
    try:
        batched([1, 2], 0)
    except ValueError:
        return
    raise AssertionError("batched([1, 2], 0) should raise ValueError as soon as it is called")
