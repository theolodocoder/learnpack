import numpy as np


def mse(pred, y) -> float:
    """Mean squared error."""
    # TODO
    ...


def mse_gradients(w: float, b: float, xs, ys) -> tuple[float, float]:
    """(dL/dw, dL/db) for L = mean((w*x + b - y)**2)."""
    # TODO: error = w * xs + b - ys, then the two means
    ...


def gradient_step(w: float, b: float, xs, ys, lr: float) -> tuple[float, float]:
    """One step of gradient descent. Returns the new (w, b)."""
    # TODO
    ...


if __name__ == "__main__":
    xs, ys = [1, 2, 3], [2, 4, 6]
    print(mse([2, 4, 6], ys))                # want 0.0
    print(mse_gradients(0.0, 0.0, xs, ys))   # want about (-18.67, -8.0)
    print(gradient_step(0.0, 0.0, xs, ys, 0.01))
