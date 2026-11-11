import numpy as np


def relu(x) -> np.ndarray:
    """max(0, x) element-wise."""
    return np.maximum(0, np.asarray(x, dtype=float))


def sigmoid(x) -> np.ndarray:
    """1 / (1 + e^(-x)) element-wise."""
    return 1.0 / (1.0 + np.exp(-np.asarray(x, dtype=float)))


def softmax(logits) -> np.ndarray:
    """Probabilities along the last axis. Stable for large logits."""
    z = np.asarray(logits, dtype=float)
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


if __name__ == "__main__":
    print(relu([-2, 0, 3]))
    print(sigmoid([0]))
    print(softmax([1, 2, 3]))
    print(softmax([1000, 1001]))
