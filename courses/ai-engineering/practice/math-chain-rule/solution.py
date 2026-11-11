import math


def sigmoid(z: float) -> float:
    """1 / (1 + e^(-z))."""
    return 1.0 / (1.0 + math.exp(-z))


def loss(w: float, x: float, y: float) -> float:
    """Squared error of a one-weight sigmoid neuron: (sigmoid(w * x) - y) ** 2."""
    return (sigmoid(w * x) - y) ** 2


def dloss_dw(w: float, x: float, y: float) -> float:
    """Derivative of loss with respect to w, by the chain rule."""
    z = w * x
    p = sigmoid(z)
    dloss_dp = 2 * (p - y)
    dp_dz = p * (1 - p)
    dz_dw = x
    return dloss_dp * dp_dz * dz_dw


if __name__ == "__main__":
    print(sigmoid(0.0))             # want 0.5
    print(loss(0.0, 2.0, 1.0))      # want 0.25
    print(dloss_dw(0.0, 2.0, 1.0))  # want -0.5
