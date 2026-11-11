import numpy as np


# ---------- Part 1: tiny semantic search ----------

def build_index(doc_vectors) -> np.ndarray:
    """Normalise every row to length 1 (zero rows stay zero), so search is one matrix multiply."""
    D = np.asarray(doc_vectors, dtype=float)
    lengths = np.linalg.norm(D, axis=1, keepdims=True)
    return np.divide(D, lengths, out=np.zeros_like(D), where=lengths > 0)


def search(index: np.ndarray, query, k: int) -> list[tuple[int, float]]:
    """Top-k (doc index, cosine score) pairs, best first; ties go to the lower index."""
    if k <= 0:
        return []
    q = np.asarray(query, dtype=float)
    n = np.linalg.norm(q)
    scores = index @ (q / n) if n > 0 else np.zeros(len(index))
    order = np.argsort(-scores, kind="stable")[:k]
    return [(int(i), float(scores[i])) for i in order]


# ---------- Part 2: a tiny network, trained from scratch ----------

def init_params(n_in: int, hidden: int, n_out: int, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    return {
        "W1": rng.normal(0, 1, size=(n_in, hidden)),
        "b1": np.zeros(hidden),
        "W2": rng.normal(0, 1 / np.sqrt(hidden), size=(hidden, n_out)),
        "b2": np.zeros(n_out),
    }


def predict(params: dict, X) -> np.ndarray:
    """Forward pass: relu hidden layer, linear output."""
    h = np.maximum(0, np.asarray(X, dtype=float) @ params["W1"] + params["b1"])
    return h @ params["W2"] + params["b2"]


def train(X, y, hidden: int = 16, lr: float = 0.1, steps: int = 2000, seed: int = 0) -> tuple[dict, list[float]]:
    """Full-batch gradient descent on mean squared error. Returns (params, loss before each step)."""
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    p = init_params(X.shape[1], hidden, y.shape[1], seed)
    losses = []
    for _ in range(steps):
        a = X @ p["W1"] + p["b1"]
        h = np.maximum(0, a)
        pred = h @ p["W2"] + p["b2"]
        losses.append(float(np.mean((pred - y) ** 2)))

        d_pred = 2 * (pred - y) / pred.size
        d_a = (d_pred @ p["W2"].T) * (a > 0)
        grads = {"W2": h.T @ d_pred, "b2": d_pred.sum(axis=0),
                 "W1": X.T @ d_a, "b1": d_a.sum(axis=0)}
        for name in p:
            p[name] -= lr * grads[name]
    return p, losses


if __name__ == "__main__":
    index = build_index([[1, 0, 0], [0.9, 0.1, 0], [0, 0, 1]])
    print(search(index, [1, 0, 0], 2))

    X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    y = np.array([[0], [1], [1], [0]], dtype=float)   # XOR
    params, losses = train(X, y)
    print(f"loss: {losses[0]:.3f} -> {losses[-1]:.5f}")
    print(predict(params, X).round(3).ravel())
