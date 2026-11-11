import numpy as np


def loss_and_grads(X, y, W1, b1, W2, b2) -> tuple[float, dict]:
    """Forward pass, MSE loss, then gradients of the loss for every parameter."""
    # Forward pass (keep a and h: the backward pass needs them)
    # TODO: a = ..., h = ..., pred = ..., loss = ...

    # Backward pass, from the loss back to the first layer
    # TODO: d_pred, d_W2, d_b2, d_h, d_a, d_W1, d_b1

    # TODO: return float(loss), {"W1": d_W1, "b1": d_b1, "W2": d_W2, "b2": d_b2}
    ...


if __name__ == "__main__":
    X = np.array([[1.0, 2.0]]); y = np.array([[1.0]])
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]]); b1 = np.array([0.0, 0.0])
    W2 = np.array([[1.0], [1.0]]); b2 = np.array([0.0])
    print(loss_and_grads(X, y, W1, b1, W2, b2))  # want loss 4.0 and the grads in the prompt
