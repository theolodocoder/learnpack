import math

from solution import cosine_similarity, dot, norm


def test_dot_adds_elementwise_products():
    got = dot([1, 2, 3], [4, 5, 6])
    assert got is not None, "dot returned None: did you forget to return?"
    assert math.isclose(got, 32.0), f"expected 32.0, got {got!r}"


def test_dot_rejects_different_lengths():
    try:
        dot([1, 2], [1, 2, 3])
    except ValueError:
        return
    assert False, "expected ValueError for vectors of different lengths"


def test_norm_is_pythagoras():
    for v, want in [([3, 4], 5.0), ([1, 2, 2], 3.0), ([0, 0, 0], 0.0)]:
        got = norm(v)
        assert got is not None and math.isclose(got, want), f"norm({v}): expected {want}, got {got!r}"


def test_cosine_of_same_direction_is_one_and_opposite_is_minus_one():
    got = cosine_similarity([1, 2], [2, 4])
    assert got is not None and math.isclose(got, 1.0), f"same direction: expected 1.0, got {got!r}"
    got = cosine_similarity([1, 2], [-3, -6])
    assert math.isclose(got, -1.0), f"opposite direction: expected -1.0, got {got!r}"


def test_cosine_of_perpendicular_vectors_is_zero():
    got = cosine_similarity([1, 0], [0, 1])
    assert got is not None and math.isclose(got, 0.0, abs_tol=1e-12), f"expected 0.0, got {got!r}"
    got = cosine_similarity([0.6, 0.8], [0.8, 0.6])
    assert math.isclose(got, 0.96), f"expected 0.96, got {got!r}"


def test_cosine_with_zero_vector_returns_zero():
    got = cosine_similarity([0, 0, 0], [1, 2, 3])
    assert got == 0.0, f"expected 0.0 for a zero vector, got {got!r}"
    assert type(got) is float, f"expected a plain float, got {type(got).__name__}"
    got = cosine_similarity([1, 2, 3], [0, 0, 0])
    assert got == 0.0, f"expected 0.0 when the second vector is zero, got {got!r}"
