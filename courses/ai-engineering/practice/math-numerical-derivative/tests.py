import math

import numpy as np

from solution import numerical_derivative, numerical_gradient


def test_derivative_of_x_squared():
    got = numerical_derivative(lambda x: x ** 2, 3.0)
    assert got is not None, "numerical_derivative returned None"
    assert math.isclose(got, 6.0, rel_tol=1e-6), f"expected about 6.0, got {got!r}"


def test_derivative_of_sin_and_exp():
    got = numerical_derivative(math.sin, 0.0)
    assert math.isclose(got, 1.0, rel_tol=1e-6), f"d/dx sin(x) at 0: expected 1.0, got {got!r}"
    got = numerical_derivative(math.exp, 1.0)
    assert math.isclose(got, math.e, rel_tol=1e-6), f"d/dx exp(x) at 1: expected {math.e:.6f}, got {got!r}"


def test_gradient_of_sum_of_squares_is_two_x():
    got = numerical_gradient(lambda v: np.sum(v ** 2), [1.0, -2.0, 0.5])
    assert got is not None, "numerical_gradient returned None"
    assert np.allclose(got, [2.0, -4.0, 1.0], atol=1e-6), f"expected [2, -4, 1], got {np.asarray(got).tolist()}"


def test_gradient_of_dot_product_is_the_other_vector():
    w = np.array([0.3, -1.2, 2.0, 0.0])
    got = numerical_gradient(lambda x: w @ x, np.array([5.0, 1.0, -1.0, 2.0]))
    assert np.allclose(got, w, atol=1e-6), f"gradient of w·x with respect to x is w = {w.tolist()}, got {np.asarray(got).tolist()}"


def test_works_on_2d_and_integer_input_without_changing_it():
    x = np.array([[1, 2], [3, 4]])
    got = numerical_gradient(lambda m: np.sum(m ** 3), x)
    assert np.shape(got) == (2, 2), f"gradient should have the same shape as x (2, 2), got {np.shape(got)}"
    assert np.allclose(got, 3 * x ** 2, rtol=1e-5), f"expected {(3 * x ** 2).tolist()}, got {np.asarray(got).tolist()}"
    assert x.tolist() == [[1, 2], [3, 4]], "numerical_gradient must not change the caller's x"
