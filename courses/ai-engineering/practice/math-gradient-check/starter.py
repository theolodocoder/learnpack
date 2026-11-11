import numpy as np


def numerical_grad(f, param, eps: float = 1e-5) -> np.ndarray:
    """Central-difference gradient of f at param, one entry at a time. Leaves param unchanged."""
    # TODO: param = np.array(param, dtype=float); loop with np.ndindex(param.shape)
    ...


def gradient_check(f, param, analytic, eps: float = 1e-5) -> float:
    """Largest relative error between `analytic` and the numerical gradient."""
    # TODO
    ...


if __name__ == "__main__":
    f = lambda p: np.sum(p ** 2)
    p = np.array([1.0, -2.0, 3.0])
    print(gradient_check(f, p, 2 * p))  # tiny
    print(gradient_check(f, p, 3 * p))  # 0.2
