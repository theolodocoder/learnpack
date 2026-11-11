import numpy as np


def normalize_rows(M) -> np.ndarray:
    """Return a copy of 2-D array M with every row scaled to length 1 (zero rows stay zero)."""
    M = np.asarray(M, dtype=float)
    lengths = np.linalg.norm(M, axis=1, keepdims=True)
    return np.divide(M, lengths, out=np.zeros_like(M), where=lengths > 0)


def similarity_matrix(queries, docs) -> np.ndarray:
    """(q, d) and (n, d) -> (q, n) matrix of cosine similarities, using one matrix multiply."""
    return normalize_rows(queries) @ normalize_rows(docs).T


if __name__ == "__main__":
    Q = [[1, 0], [0, 1]]
    D = [[2, 0], [1, 1], [0, 0]]
    print(similarity_matrix(Q, D))
