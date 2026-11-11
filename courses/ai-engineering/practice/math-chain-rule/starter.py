import math


def sigmoid(z: float) -> float:
    """1 / (1 + e^(-z))."""
    # TODO
    ...


def loss(w: float, x: float, y: float) -> float:
    """Squared error of a one-weight sigmoid neuron: (sigmoid(w * x) - y) ** 2."""
    # TODO
    ...


def dloss_dw(w: float, x: float, y: float) -> float:
    """Derivative of loss with respect to w, by the chain rule."""
    # TODO: compute z and p (the forward pass), then multiply the three local derivatives
    ...


if __name__ == "__main__":
    print(sigmoid(0.0))             # want 0.5
    print(loss(0.0, 2.0, 1.0))      # want 0.25
    print(dloss_dw(0.0, 2.0, 1.0))  # want -0.5
