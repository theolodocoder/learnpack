import numpy as np


def numerical_grad(f, param, eps: float = 1e-5) -> np.ndarray:
    """Central-difference gradient of f at param, one entry at a time. Leaves param unchanged."""
    param = np.array(param, dtype=float)
    grad = np.zeros_like(param)
    for i in np.ndindex(param.shape):
        plus, minus = param.copy(), param.copy()
        plus[i] += eps
        minus[i] -= eps
        grad[i] = (f(plus) - f(minus)) / (2 * eps)
    return grad


def gradient_check(f, param, analytic, eps: float = 1e-5) -> float:
    """Largest relative error between `analytic` and the numerical gradient."""
    num = numerical_grad(f, param, eps)
    analytic = np.asarray(analytic, dtype=float)
    rel = np.abs(analytic - num) / np.maximum(np.abs(analytic) + np.abs(num), 1e-12)
    return float(rel.max())


if __name__ == "__main__":
    f = lambda p: np.sum(p ** 2)
    p = np.array([1.0, -2.0, 3.0])
    print(gradient_check(f, p, 2 * p))  # tiny
    print(gradient_check(f, p, 3 * p))  # 0.2
