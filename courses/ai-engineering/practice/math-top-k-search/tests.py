import numpy as np

from solution import top_k

DOCS = [[1, 0], [0.9, 0.1], [0, 1], [-1, 0]]


def test_returns_best_matches_first():
    got = top_k([1, 0], DOCS, 2)
    assert got == [0, 1], f"expected [0, 1], got {got!r}"


def test_uses_cosine_not_raw_dot_product():
    # The long vector [10, 10] has a bigger dot product with the query, but
    # [1, 0.1] points in almost the same direction, so it should win.
    docs = [[10, 10], [1, 0.1]]
    got = top_k([1, 0], docs, 1)
    assert got == [1], f"expected [1] (closest direction), got {got!r}. Did you divide by the lengths?"


def test_returns_plain_ints_in_a_list():
    got = top_k(np.array([0.0, 1.0]), np.array(DOCS), 3)
    assert isinstance(got, list), f"expected a list, got {type(got).__name__}"
    assert all(type(i) is int for i in got), f"expected Python ints, got {[type(i).__name__ for i in got]}"
    assert got == [2, 1, 0], f"expected [2, 1, 0], got {got!r}"


def test_k_larger_than_number_of_docs_returns_all_ranked():
    got = top_k([1, 0], DOCS, 10)
    assert got == [0, 1, 2, 3], f"expected [0, 1, 2, 3], got {got!r}"


def test_zero_k_and_zero_vectors():
    assert top_k([1, 0], DOCS, 0) == [], "k=0 should return []"
    got = top_k([1, 0], [[0, 0], [-1, 0], [2, 0]], 3)
    assert got == [2, 0, 1], f"a zero doc scores 0.0, so expected [2, 0, 1], got {got!r}"


def test_ties_keep_lower_index_first():
    got = top_k([1, 1], [[0, 1], [2, 2], [1, 1], [1, 0]], 4)
    assert got == [1, 2, 0, 3], f"expected [1, 2, 0, 3] (ties by index), got {got!r}"
