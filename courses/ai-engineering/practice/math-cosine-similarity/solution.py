import math

import numpy as np


def dot(a: list[float], b: list[float]) -> float:
    """Sum of element-wise products. Raise ValueError if lengths differ. Plain Python only."""
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} vs {len(b)}")
    return float(sum(x * y for x, y in zip(a, b)))


def norm(a: list[float]) -> float:
    """Length of the vector: the square root of the sum of squares. Plain Python only."""
    return math.sqrt(sum(x * x for x in a))


def cosine_similarity(a, b) -> float:
    """(a · b) / (|a| * |b|) with NumPy. Return 0.0 if either vector is all zeros."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(a @ b / (na * nb))


if __name__ == "__main__":
    print(dot([1, 2, 3], [4, 5, 6]))          # want 32.0
    print(norm([3, 4]))                       # want 5.0
    print(cosine_similarity([1, 2], [2, 4]))  # want 1.0
    print(cosine_similarity([0, 0], [1, 1]))  # want 0.0
