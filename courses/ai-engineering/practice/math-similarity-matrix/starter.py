import numpy as np


def normalize_rows(M) -> np.ndarray:
    """Return a copy of 2-D array M with every row scaled to length 1 (zero rows stay zero)."""
    # TODO: M = np.asarray(M, dtype=float)
    # TODO: lengths with keepdims=True so the shape is (rows, 1)
    # TODO: divide, leaving zero rows as zeros
    ...


def similarity_matrix(queries, docs) -> np.ndarray:
    """(q, d) and (n, d) -> (q, n) matrix of cosine similarities, using one matrix multiply."""
    # TODO: normalize both, then multiply queries by the transpose of docs
    ...


if __name__ == "__main__":
    Q = [[1, 0], [0, 1]]
    D = [[2, 0], [1, 1], [0, 0]]
    print(similarity_matrix(Q, D))
