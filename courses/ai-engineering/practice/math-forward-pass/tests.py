import warnings

import numpy as np

from solution import forward

W1 = np.array([[1.0, -1.0], [0.5, 1.0]])
B1 = np.array([0.0, -2.0])
W2 = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 1.0]])
B2 = np.zeros(3)


def _reference(x, W1, b1, W2, b2):
    h = np.maximum(0, x @ W1 + b1)
    z = h @ W2 + b2
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def test_single_example_matches_worked_example():
    got = forward(np.array([1.0, 2.0]), W1, B1, W2, B2)
    assert got is not None, "forward returned None"
    want = np.exp([2, 0, -2]) / np.exp([2, 0, -2]).sum()
    assert np.shape(got) == (3,), f"one example should give shape (3,), got {np.shape(got)}"
    assert np.allclose(got, want), f"expected {want.round(4).tolist()}, got {np.asarray(got).round(4).tolist()}"


def test_relu_is_applied_to_the_hidden_layer():
    # Without relu, the hidden unit at -1 would leak through and change the answer.
    got = forward(np.array([1.0, 2.0]), W1, B1, W2, B2)
    no_relu = W2.T @ (np.array([1.0, 2.0]) @ W1 + B1)
    leaked = np.exp(no_relu) / np.exp(no_relu).sum()
    assert not np.allclose(got, leaked), "looks like relu wasn't applied to the hidden layer"


def test_batch_gives_one_row_of_probabilities_per_example():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(6, 4))
    w1, b1 = rng.normal(size=(4, 5)), rng.normal(size=5)
    w2, b2 = rng.normal(size=(5, 3)), rng.normal(size=3)
    got = forward(X, w1, b1, w2, b2)
    assert np.shape(got) == (6, 3), f"expected shape (6, 3), got {np.shape(got)}"
    assert np.allclose(np.sum(got, axis=1), 1.0), "each row of probabilities should sum to 1"
    assert np.allclose(got, _reference(X, w1, b1, w2, b2)), "batch output doesn't match the expected forward pass"


def test_batch_row_equals_single_example():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(3, 2))
    batch = forward(X, W1, B1, W2, B2)
    single = forward(X[1], W1, B1, W2, B2)
    assert np.allclose(batch[1], single), "row 1 of the batch should equal forward() on example 1 alone"


def test_large_weights_do_not_produce_nan():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        got = forward(np.array([1.0, 2.0]), W1 * 500, B1, W2 * 500, B2)
    assert not np.isnan(got).any(), "got nan with large logits: make softmax stable"
    assert np.allclose(np.sum(got), 1.0), "probabilities should still sum to 1"
