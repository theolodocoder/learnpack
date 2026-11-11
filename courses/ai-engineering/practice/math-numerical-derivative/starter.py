import numpy as np


def numerical_derivative(f, x: float, h: float = 1e-5) -> float:
    """Central-difference estimate of f'(x)."""
    # TODO: (f(x + h) - f(x - h)) / (2 * h), as a float
    ...


def numerical_gradient(f, x, h: float = 1e-5) -> np.ndarray:
    """Estimate the gradient of f (array -> number) at x, one coordinate at a time."""
    # TODO 1: x = np.array(x, dtype=float)  (a float copy)
    # TODO 2: grad = np.zeros_like(x)
    # TODO 3: for each index i (np.ndindex(x.shape) handles any shape):
    #           make two copies, add h to one at i, subtract h from the other,
    #           grad[i] = (f(plus) - f(minus)) / (2 * h)
    ...


if __name__ == "__main__":
    print(numerical_derivative(lambda x: x ** 2, 3.0))                 # want about 6.0
    print(numerical_gradient(lambda v: np.sum(v ** 2), [1.0, -2.0]))   # want about [2, -4]
