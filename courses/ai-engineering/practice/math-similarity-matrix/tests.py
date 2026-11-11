import numpy as np

from solution import normalize_rows, similarity_matrix


def test_normalized_rows_have_length_one():
    M = np.array([[3.0, 4.0], [1.0, 0.0], [2.0, 2.0]])
    got = normalize_rows(M)
    assert got is not None, "normalize_rows returned None"
    assert np.allclose(np.linalg.norm(got, axis=1), 1.0), f"every row should have length 1, got {np.asarray(got).tolist()}"
    assert np.allclose(got[0], [0.6, 0.8]), f"[3, 4] should become [0.6, 0.8], got {got[0].tolist()}"
    assert np.allclose(M[0], [3.0, 4.0]), "normalize_rows should not modify its input"


def test_zero_rows_stay_zero_without_nan():
    got = normalize_rows([[0, 0], [5, 0]])
    assert not np.isnan(got).any(), f"found nan: {np.asarray(got).tolist()}"
    assert np.allclose(got, [[0, 0], [1, 0]]), f"expected [[0, 0], [1, 0]], got {np.asarray(got).tolist()}"


def test_small_example():
    got = similarity_matrix([[1, 0], [0, 1]], [[2, 0], [1, 1], [0, 0]])
    want = np.array([[1, 2 ** -0.5, 0], [0, 2 ** -0.5, 0]])
    assert got is not None, "similarity_matrix returned None"
    assert np.shape(got) == (2, 3), f"expected shape (2, 3), got {np.shape(got)}"
    assert np.allclose(got, want), f"expected {want.round(4).tolist()}, got {np.asarray(got).round(4).tolist()}"


def test_matches_one_at_a_time_cosine_on_random_embeddings():
    rng = np.random.default_rng(42)
    Q = rng.normal(size=(5, 16))
    D = rng.normal(size=(40, 16))
    got = similarity_matrix(Q, D)
    assert np.shape(got) == (5, 40), f"expected shape (5, 40), got {np.shape(got)}"
    for i in range(5):
        for j in range(40):
            want = Q[i] @ D[j] / (np.linalg.norm(Q[i]) * np.linalg.norm(D[j]))
            assert np.isclose(got[i, j], want), f"entry [{i}, {j}]: expected {want:.6f}, got {got[i, j]:.6f}"


def test_every_score_is_between_minus_one_and_one():
    rng = np.random.default_rng(7)
    got = similarity_matrix(rng.normal(size=(8, 32)) * 100, rng.normal(size=(20, 32)))
    assert np.all(got <= 1 + 1e-9) and np.all(got >= -1 - 1e-9), "cosine similarities must lie in [-1, 1]"
