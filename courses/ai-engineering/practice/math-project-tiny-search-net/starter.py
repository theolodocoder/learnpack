import numpy as np


# ---------- Part 1: tiny semantic search ----------

def build_index(doc_vectors) -> np.ndarray:
    """Normalise every row to length 1 (zero rows stay zero), so search is one matrix multiply."""
    # TODO
    ...


def search(index: np.ndarray, query, k: int) -> list[tuple[int, float]]:
    """Top-k (doc index, cosine score) pairs, best first; ties go to the lower index."""
    # TODO: handle k <= 0 and a zero query, then index @ unit_query, argsort, slice
    ...


# ---------- Part 2: a tiny network, trained from scratch ----------

def init_params(n_in: int, hidden: int, n_out: int, seed: int = 0) -> dict:
    """Written for you: small random weights, zero biases."""
    rng = np.random.default_rng(seed)
    return {
        "W1": rng.normal(0, 1, size=(n_in, hidden)),
        "b1": np.zeros(hidden),
        "W2": rng.normal(0, 1 / np.sqrt(hidden), size=(hidden, n_out)),
        "b2": np.zeros(n_out),
    }


def predict(params: dict, X) -> np.ndarray:
    """Forward pass: relu hidden layer, linear output."""
    # TODO
    ...


def train(X, y, hidden: int = 16, lr: float = 0.1, steps: int = 2000, seed: int = 0) -> tuple[dict, list[float]]:
    """Full-batch gradient descent on mean squared error. Returns (params, loss before each step)."""
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    p = init_params(X.shape[1], hidden, y.shape[1], seed)
    losses = []
    for _ in range(steps):
        # TODO 1: forward pass (keep a and h), append the loss as a float
        # TODO 2: backward pass: d_pred, then grads for W2, b2, W1, b1
        # TODO 3: p[name] -= lr * grads[name] for each parameter
        pass
    return p, losses


if __name__ == "__main__":
    index = build_index([[1, 0, 0], [0.9, 0.1, 0], [0, 0, 1]])
    print(search(index, [1, 0, 0], 2))

    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    y = np.array([[0], [1], [1], [0]], dtype=float)   # XOR
    params, losses = train(X, y)
    if losses:
        print(f"loss: {losses[0]:.3f} -> {losses[-1]:.5f}")
    print(predict(params, X))
