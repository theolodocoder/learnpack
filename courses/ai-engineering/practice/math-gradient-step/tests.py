import math

import numpy as np

from solution import gradient_step, mse, mse_gradients

XS, YS = [1, 2, 3], [2, 4, 6]


def test_mse_values():
    assert mse([2, 4, 6], YS) == 0.0, f"perfect predictions: expected 0.0, got {mse([2, 4, 6], YS)!r}"
    got = mse([1, 2, 3], [2, 4, 6])
    assert got is not None and math.isclose(got, 14 / 3), f"expected {14 / 3:.4f}, got {got!r}"


def test_gradients_match_worked_example():
    got = mse_gradients(0.0, 0.0, XS, YS)
    assert got is not None, "mse_gradients returned None"
    dw, db = got
    assert math.isclose(dw, -56 / 3), f"dL/dw: expected {-56 / 3:.4f}, got {dw!r}"
    assert math.isclose(db, -8.0), f"dL/db: expected -8.0, got {db!r}"


def test_gradients_match_numerical_derivatives():
    rng = np.random.default_rng(0)
    xs, ys = rng.normal(size=20), rng.normal(size=20)
    w, b, h = 0.7, -0.3, 1e-6
    L = lambda w, b: np.mean((w * xs + b - ys) ** 2)
    dw, db = mse_gradients(w, b, xs, ys)
    want_dw = (L(w + h, b) - L(w - h, b)) / (2 * h)
    want_db = (L(w, b + h) - L(w, b - h)) / (2 * h)
    assert math.isclose(dw, want_dw, rel_tol=1e-5), f"dL/dw: numerical says {want_dw:.6f}, got {dw!r}"
    assert math.isclose(db, want_db, rel_tol=1e-5), f"dL/db: numerical says {want_db:.6f}, got {db!r}"


def test_step_moves_against_the_gradient():
    got = gradient_step(0.0, 0.0, XS, YS, 0.01)
    assert got is not None, "gradient_step returned None"
    w, b = got
    assert math.isclose(w, 0.56 / 3), f"expected w = {0.56 / 3:.5f}, got {w!r} (did you subtract lr * gradient?)"
    assert math.isclose(b, 0.08), f"expected b = 0.08, got {b!r}"


def test_a_small_step_lowers_the_loss():
    w, b = 0.0, 0.0
    before = mse(np.asarray(XS) * w + b, YS)
    w, b = gradient_step(w, b, XS, YS, 0.01)
    after = mse(np.asarray(XS) * w + b, YS)
    assert after < before, f"loss should go down after a small step: before {before:.4f}, after {after:.4f}"


def test_at_the_minimum_the_step_changes_nothing():
    w, b = gradient_step(2.0, 0.0, XS, YS, 0.1)
    assert math.isclose(w, 2.0) and math.isclose(b, 0.0, abs_tol=1e-12), f"at the perfect fit the gradient is 0, so expected (2.0, 0.0), got {(w, b)!r}"
