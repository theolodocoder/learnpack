import numpy as np


def relu(x) -> np.ndarray:
    """max(0, x) element-wise."""
    # TODO
    ...


def sigmoid(x) -> np.ndarray:
    """1 / (1 + e^(-x)) element-wise."""
    # TODO
    ...


def softmax(logits) -> np.ndarray:
    """Probabilities along the last axis. Stable for large logits."""
    # TODO 1: z = np.asarray(logits, dtype=float)
    # TODO 2: subtract z.max(axis=-1, keepdims=True)
    # TODO 3: exponentiate and divide by the sum along the last axis (keepdims=True)
    ...


if __name__ == "__main__":
    print(relu([-2, 0, 3]))
    print(sigmoid([0]))
    print(softmax([1, 2, 3]))
    print(softmax([1000, 1001]))
