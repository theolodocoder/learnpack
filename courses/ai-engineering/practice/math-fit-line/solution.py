import numpy as np


def fit_line(xs, ys, lr: float = 0.1, steps: int = 1000) -> tuple[float, float]:
    """Fit y ≈ w*x + b by gradient descent on mean squared error, starting from w = b = 0."""
    xs, ys = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
    w, b = 0.0, 0.0
    for _ in range(steps):
        error = w * xs + b - ys
        w -= lr * np.mean(2 * error * xs)
        b -= lr * np.mean(2 * error)
    return float(w), float(b)


if __name__ == "__main__":
    print(fit_line([0, 1, 2, 3], [1, 3, 5, 7], lr=0.05, steps=2000))  # want about (2.0, 1.0)
