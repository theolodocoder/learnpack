import numpy as np


def top_k(query, docs, k: int) -> list[int]:
    """Indices of the k docs most cosine-similar to query, best first."""
    # TODO 1: convert to float arrays with np.asarray(..., dtype=float)
    # TODO 2: compute the length of each doc row (axis=1) and of the query
    # TODO 3: scores = (docs @ query) / (doc_lengths * query_length), with 0.0 where a length is 0
    # TODO 4: order = np.argsort(-scores, kind="stable"); return the first k as a list of ints
    ...


if __name__ == "__main__":
    docs = [[1, 0], [0.9, 0.1], [0, 1], [-1, 0]]
    print(top_k([1, 0], docs, 2))   # want [0, 1]
    print(top_k([1, 0], docs, 10))  # want [0, 1, 2, 3]
