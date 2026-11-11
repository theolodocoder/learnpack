import math

import numpy as np

from solution import fit_line


def test_recovers_a_perfect_line():
    w, b = fit_line([0, 1, 2, 3], [1, 3, 5, 7], lr=0.05, steps=2000)
    assert math.isclose(w, 2.0, abs_tol=1e-3) and math.isclose(b, 1.0, abs_tol=1e-3), f"expected about (2.0, 1.0), got {(w, b)!r}"


def test_matches_least_squares_on_noisy_data():
    rng = np.random.default_rng(1)
    xs = rng.uniform(-2, 2, size=50)
    ys = -1.5 * xs + 0.7 + rng.normal(scale=0.3, size=50)
    w, b = fit_line(xs, ys, lr=0.1, steps=3000)
    want_w, want_b = np.polyfit(xs, ys, 1)
    assert math.isclose(w, want_w, abs_tol=1e-4) and math.isclose(b, want_b, abs_tol=1e-4), (
        f"expected about ({want_w:.4f}, {want_b:.4f}), got ({w:.4f}, {b:.4f})")


def test_zero_steps_returns_the_starting_point():
    got = fit_line([1, 2, 3], [2, 4, 6], lr=0.1, steps=0)
    assert got == (0.0, 0.0), f"with no steps, expected (0.0, 0.0), got {got!r}"


def test_returns_plain_floats():
    w, b = fit_line([0, 1, 2], [1, 2, 3], lr=0.1, steps=10)
    assert type(w) is float and type(b) is float, f"expected two floats, got {type(w).__name__}, {type(b).__name__}"


def test_too_small_a_learning_rate_barely_moves():
    w, b = fit_line([0, 1, 2, 3], [1, 3, 5, 7], lr=1e-5, steps=100)
    assert 0 < w < 0.05 and 0 < b < 0.05, f"with lr=1e-5 for 100 steps the line should move only a little towards (2, 1), got {(w, b)!r}"
