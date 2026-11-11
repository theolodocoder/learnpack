import numpy as np


def loss_and_grads(X, y, W1, b1, W2, b2) -> tuple[float, dict]:
    """Forward pass, MSE loss, then gradients of the loss for every parameter."""
    a = X @ W1 + b1
    h = np.maximum(0, a)
    pred = h @ W2 + b2
    loss = np.mean((pred - y) ** 2)

    d_pred = 2 * (pred - y) / pred.size
    d_W2 = h.T @ d_pred
    d_b2 = d_pred.sum(axis=0)
    d_h = d_pred @ W2.T
    d_a = d_h * (a > 0)
    d_W1 = X.T @ d_a
    d_b1 = d_a.sum(axis=0)
    return float(loss), {"W1": d_W1, "b1": d_b1, "W2": d_W2, "b2": d_b2}


if __name__ == "__main__":
    X = np.array([[1.0, 2.0]]); y = np.array([[1.0]])
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]]); b1 = np.array([0.0, 0.0])
    W2 = np.array([[1.0], [1.0]]); b2 = np.array([0.0])
    print(loss_and_grads(X, y, W1, b1, W2, b2))  # want loss 4.0 and the grads in the prompt
