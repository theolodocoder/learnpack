import numpy as np


def top_k(query, docs, k: int) -> list[int]:
    """Indices of the k docs most cosine-similar to query, best first."""
    if k <= 0:
        return []
    q = np.asarray(query, dtype=float)
    D = np.asarray(docs, dtype=float)
    lengths = np.linalg.norm(D, axis=1) * np.linalg.norm(q)
    raw = D @ q
    scores = np.divide(raw, lengths, out=np.zeros_like(raw), where=lengths > 0)
    order = np.argsort(-scores, kind="stable")
    return [int(i) for i in order[:k]]


if __name__ == "__main__":
    docs = [[1, 0], [0.9, 0.1], [0, 1], [-1, 0]]
    print(top_k([1, 0], docs, 2))   # want [0, 1]
    print(top_k([1, 0], docs, 10))  # want [0, 1, 2, 3]
