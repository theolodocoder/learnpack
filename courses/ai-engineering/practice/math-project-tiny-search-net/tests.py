import math

import numpy as np

from solution import build_index, predict, search, train

XOR_X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
XOR_Y = np.array([[0], [1], [1], [0]], dtype=float)


def test_index_rows_have_unit_length_and_zero_rows_stay_zero():
    got = build_index([[3, 4], [0, 0], [0, 2]])
    assert got is not None, "build_index returned None"
    assert not np.isnan(got).any(), "found nan in the index: skip zero rows"
    assert np.allclose(got, [[0.6, 0.8], [0, 0], [0, 1]]), f"got {np.asarray(got).tolist()}"


def test_search_returns_ranked_index_score_pairs():
    index = build_index([[1, 0, 0], [0.9, 0.1, 0], [0, 0, 1], [-1, 0, 0]])
    got = search(index, [2, 0, 0], 2)
    assert got is not None, "search returned None"
    assert [i for i, _ in got] == [0, 1], f"expected docs [0, 1], got {got!r}"
    assert all(type(i) is int and type(s) is float for i, s in got), "each result should be (int, float)"
    assert math.isclose(got[0][1], 1.0) and math.isclose(got[1][1], 0.9 / math.sqrt(0.82)), f"scores should be cosine similarities, got {got!r}"


def test_search_edge_cases():
    index = build_index([[1, 0], [0, 1], [1, 1]])
    got = search(index, [1, 0], 10)
    assert [i for i, _ in got] == [0, 2, 1], f"k > n should return every doc ranked, got {got!r}"
    assert search(index, [1, 0], 0) == [], "k = 0 should return []"
    got = search(index, [0, 0], 3)
    assert [s for _, s in got] == [0.0, 0.0, 0.0] and [i for i, _ in got] == [0, 1, 2], f"a zero query scores 0.0 everywhere (ties by index), got {got!r}"


def test_predict_shape():
    rng = np.random.default_rng(0)
    params = {"W1": rng.normal(size=(2, 5)), "b1": np.zeros(5), "W2": rng.normal(size=(5, 3)), "b2": np.ones(3)}
    got = predict(params, XOR_X)
    assert np.shape(got) == (4, 3), f"expected shape (4, 3), got {np.shape(got)}"
    want = np.maximum(0, XOR_X @ params["W1"]) @ params["W2"] + 1
    assert np.allclose(got, want), "predict should be relu(X @ W1 + b1) @ W2 + b2"


def test_training_records_one_falling_loss_per_step():
    _, losses = train(XOR_X, XOR_Y, steps=300)
    assert len(losses) == 300, f"expected 300 losses, got {len(losses)}"
    assert all(type(l) is float for l in losses), "each loss should be a float"
    assert losses[-1] < losses[0] * 0.5, f"loss should fall a lot: first {losses[0]:.4f}, last {losses[-1]:.4f}"


def test_network_learns_xor():
    params, losses = train(XOR_X, XOR_Y, hidden=16, lr=0.1, steps=2000, seed=0)
    assert losses[-1] < 1e-3, f"final loss should be below 0.001, got {losses[-1]:.5f}"
    pred = predict(params, XOR_X)
    assert np.array_equal((pred > 0.5).astype(int), XOR_Y.astype(int)), f"expected XOR outputs [0, 1, 1, 0], got {pred.round(3).ravel().tolist()}"
