import numpy as np


def relu(x):
    # TODO (copy from the activations exercise)
    ...


def softmax(logits):
    # TODO (stable, along the last axis)
    ...


def forward(x, W1, b1, W2, b2) -> np.ndarray:
    """Two-layer network: relu hidden layer, softmax output. Works for one example or a batch."""
    # TODO: h = relu(x @ W1 + b1); logits = h @ W2 + b2; return softmax(logits)
    ...


if __name__ == "__main__":
    x = np.array([1.0, 2.0])
    W1 = np.array([[1.0, -1.0], [0.5, 1.0]])
    b1 = np.array([0.0, -2.0])
    W2 = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 1.0]])
    b2 = np.zeros(3)
    print(forward(x, W1, b1, W2, b2))  # want about [0.8668, 0.1173, 0.0159]
