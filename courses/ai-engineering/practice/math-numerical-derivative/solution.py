import numpy as np


def numerical_derivative(f, x: float, h: float = 1e-5) -> float:
    """Central-difference estimate of f'(x)."""
    return float((f(x + h) - f(x - h)) / (2 * h))


def numerical_gradient(f, x, h: float = 1e-5) -> np.ndarray:
    """Estimate the gradient of f (array -> number) at x, one coordinate at a time."""
    x = np.array(x, dtype=float)
    grad = np.zeros_like(x)
    for i in np.ndindex(x.shape):
        plus, minus = x.copy(), x.copy()
        plus[i] += h
        minus[i] -= h
        grad[i] = (f(plus) - f(minus)) / (2 * h)
    return grad


if __name__ == "__main__":
    print(numerical_derivative(lambda x: x ** 2, 3.0))                 # want about 6.0
    print(numerical_gradient(lambda v: np.sum(v ** 2), [1.0, -2.0]))   # want about [2, -4]
