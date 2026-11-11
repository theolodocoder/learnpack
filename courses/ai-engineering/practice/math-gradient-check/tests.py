import math

import numpy as np

from solution import gradient_check, numerical_grad


def test_numerical_grad_of_sum_of_squares():
    p = np.array([1.0, -2.0, 3.0])
    got = numerical_grad(lambda q: np.sum(q ** 2), p)
    assert got is not None, "numerical_grad returned None"
    assert np.allclose(got, 2 * p, atol=1e-6), f"expected {(2 * p).tolist()}, got {np.asarray(got).tolist()}"


def test_numerical_grad_handles_matrices_and_leaves_param_alone():
    W = np.array([[1.0, 2.0], [3.0, 4.0]])
    x = np.array([0.5, -1.0])
    got = numerical_grad(lambda M: np.sum(M @ x), W)
    assert np.shape(got) == (2, 2), f"expected shape (2, 2), got {np.shape(got)}"
    assert np.allclose(got, [[0.5, -1.0], [0.5, -1.0]], atol=1e-6), f"got {np.asarray(got).tolist()}"
    assert W.tolist() == [[1.0, 2.0], [3.0, 4.0]], "numerical_grad must not change param"


def test_correct_gradient_passes():
    p = np.array([1.0, -2.0, 3.0])
    err = gradient_check(lambda q: np.sum(q ** 2), p, 2 * p)
    assert err is not None, "gradient_check returned None"
    assert type(err) is float, f"expected a float, got {type(err).__name__}"
    assert err < 1e-7, f"a correct gradient should have tiny error, got {err:.2e}"


def test_wrong_gradient_is_caught():
    p = np.array([1.0, -2.0, 3.0])
    err = gradient_check(lambda q: np.sum(q ** 2), p, 3 * p)
    assert math.isclose(err, 0.2, rel_tol=1e-4), f"expected relative error 0.2, got {err!r}"


def test_checks_a_real_layer():
    rng = np.random.default_rng(5)
    X, y = rng.normal(size=(6, 3)), rng.normal(size=6)
    w = rng.normal(size=3)
    loss = lambda w: np.mean((np.tanh(X @ w) - y) ** 2)
    t = np.tanh(X @ w)
    right = X.T @ (2 * (t - y) * (1 - t ** 2)) / len(y)
    wrong = X.T @ (2 * (t - y)) / len(y)    # forgot the tanh derivative
    assert gradient_check(loss, w, right) < 1e-6, "the correct tanh-layer gradient should pass"
    assert gradient_check(loss, w, wrong) > 1e-3, "the gradient missing tanh' should fail the check"


def test_zero_gradients_do_not_divide_by_zero():
    err = gradient_check(lambda q: 5.0, np.array([1.0, 2.0]), np.zeros(2))
    assert err == 0.0, f"a constant function has zero gradient everywhere, expected 0.0, got {err!r}"
