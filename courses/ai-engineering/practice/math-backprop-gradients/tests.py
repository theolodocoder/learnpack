import math

import numpy as np

from solution import loss_and_grads


def _params(seed, d=3, hidden=4, out=2, n=5):
    rng = np.random.default_rng(seed)
    return (rng.normal(size=(n, d)), rng.normal(size=(n, out)),
            rng.normal(size=(d, hidden)), rng.normal(size=hidden),
            rng.normal(size=(hidden, out)), rng.normal(size=out))


def _loss(X, y, W1, b1, W2, b2):
    return np.mean((np.maximum(0, X @ W1 + b1) @ W2 + b2 - y) ** 2)


def _numeric(args, idx, h=1e-6):
    args = [a.copy() for a in args]
    p = args[idx]
    grad = np.zeros_like(p)
    for i in np.ndindex(p.shape):
        old = p[i]
        p[i] = old + h; up = _loss(*args)
        p[i] = old - h; down = _loss(*args)
        p[i] = old
        grad[i] = (up - down) / (2 * h)
    return grad


def test_worked_example():
    X = np.array([[1.0, 2.0]]); y = np.array([[1.0]])
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]]); b1 = np.zeros(2)
    W2 = np.array([[1.0], [1.0]]); b2 = np.zeros(1)
    got = loss_and_grads(X, y, W1, b1, W2, b2)
    assert got is not None, "loss_and_grads returned None"
    loss, g = got
    assert math.isclose(loss, 4.0), f"expected loss 4.0, got {loss!r}"
    assert np.allclose(g["W2"], [[8], [4]]), f"W2 grad: expected [[8], [4]], got {np.asarray(g['W2']).tolist()}"
    assert np.allclose(g["b2"], [4]), f"b2 grad: expected [4], got {np.asarray(g['b2']).tolist()}"
    assert np.allclose(g["W1"], [[4, 4], [8, 8]]), f"W1 grad: expected [[4, 4], [8, 8]], got {np.asarray(g['W1']).tolist()}"
    assert np.allclose(g["b1"], [4, 4]), f"b1 grad: expected [4, 4], got {np.asarray(g['b1']).tolist()}"


def test_gradients_have_the_same_shapes_as_parameters():
    X, y, W1, b1, W2, b2 = _params(0)
    loss, g = loss_and_grads(X, y, W1, b1, W2, b2)
    for name, p in [("W1", W1), ("b1", b1), ("W2", W2), ("b2", b2)]:
        assert name in g, f"missing key {name!r} in grads"
        assert np.shape(g[name]) == p.shape, f"grads[{name!r}] has shape {np.shape(g[name])}, expected {p.shape}"
    assert math.isclose(loss, _loss(X, y, W1, b1, W2, b2)), f"loss should be {_loss(X, y, W1, b1, W2, b2):.6f}, got {loss!r}"


def test_output_layer_gradients_match_numerical():
    args = _params(1)
    _, g = loss_and_grads(*args)
    for name, idx in [("W2", 4), ("b2", 5)]:
        want = _numeric(args, idx)
        assert np.allclose(g[name], want, atol=1e-6), f"grads[{name!r}] is off.\nnumerical: {want.round(5).tolist()}\nyours:     {np.asarray(g[name]).round(5).tolist()}"


def test_hidden_layer_gradients_match_numerical():
    args = _params(2)
    _, g = loss_and_grads(*args)
    for name, idx in [("W1", 2), ("b1", 3)]:
        want = _numeric(args, idx)
        assert np.allclose(g[name], want, atol=1e-6), f"grads[{name!r}] is off (check the relu mask and the transposes).\nnumerical: {want.round(5).tolist()}\nyours:     {np.asarray(g[name]).round(5).tolist()}"


def test_dead_hidden_units_get_zero_gradient():
    X, y, W1, b1, W2, b2 = _params(3)
    b1 = b1.copy(); b1[0] = -100.0   # unit 0 is negative for every input, so relu outputs 0
    _, g = loss_and_grads(X, y, W1, b1, W2, b2)
    assert np.allclose(g["W1"][:, 0], 0) and math.isclose(g["b1"][0], 0.0, abs_tol=1e-12), "a unit that relu switched off should get zero gradient"
    assert np.allclose(g["W2"][0], 0), "W2 rows reading from a dead unit should get zero gradient"
