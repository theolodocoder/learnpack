import math

from solution import dloss_dw, loss, sigmoid


def _numeric(w, x, y, h=1e-6):
    return (loss(w + h, x, y) - loss(w - h, x, y)) / (2 * h)


def test_sigmoid_values():
    for z, want in [(0.0, 0.5), (2.0, 0.8807970779778823), (-2.0, 0.11920292202211755)]:
        got = sigmoid(z)
        assert got is not None and math.isclose(got, want, rel_tol=1e-9), f"sigmoid({z}): expected {want}, got {got!r}"


def test_loss_matches_example():
    got = loss(0.0, 2.0, 1.0)
    assert got is not None and math.isclose(got, 0.25), f"expected 0.25, got {got!r}"


def test_gradient_matches_worked_example():
    got = dloss_dw(0.0, 2.0, 1.0)
    assert got is not None and math.isclose(got, -0.5), f"expected -0.5, got {got!r}"


def test_gradient_matches_numerical_derivative():
    for w, x, y in [(0.5, 1.5, 0.0), (-1.2, 0.7, 1.0), (2.0, -3.0, 0.3), (0.1, 10.0, 1.0)]:
        got = dloss_dw(w, x, y)
        want = _numeric(w, x, y)
        assert math.isclose(got, want, rel_tol=1e-5, abs_tol=1e-9), f"w={w}, x={x}, y={y}: numerical says {want:.8f}, you returned {got!r}"


def test_gradient_is_zero_when_input_is_zero():
    got = dloss_dw(1.3, 0.0, 1.0)
    assert math.isclose(got, 0.0, abs_tol=1e-12), f"with x = 0, w has no effect, so expected 0.0, got {got!r}"
