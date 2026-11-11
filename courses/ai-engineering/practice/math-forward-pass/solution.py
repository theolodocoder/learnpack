import numpy as np


def relu(x):
    return np.maximum(0, x)


def softmax(logits):
    z = np.asarray(logits, dtype=float)
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def forward(x, W1, b1, W2, b2) -> np.ndarray:
    """Two-layer network: relu hidden layer, softmax output. Works for one example or a batch."""
    h = relu(np.asarray(x, dtype=float) @ W1 + b1)
    logits = h @ W2 + b2
    return softmax(logits)


if __name__ == "__main__":
    x = np.array([1.0, 2.0])
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]])
    b1 = np.array([0.0, -2.0])
    W2 = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 1.0]])
    b2 = np.zeros(3)
    print(forward(x, W1, b1, W2, b2))  # want about [0.8668, 0.1173, 0.0159]
