import math

import numpy as np


def dot(a: list[float], b: list[float]) -> float:
    """Sum of element-wise products. Raise ValueError if lengths differ. Plain Python only."""
    # TODO: check the lengths, then add up a[i] * b[i]
    ...


def norm(a: list[float]) -> float:
    """Length of the vector: the square root of the sum of squares. Plain Python only."""
    # TODO
    ...


def cosine_similarity(a, b) -> float:
    """(a · b) / (|a| * |b|) with NumPy. Return 0.0 if either vector is all zeros."""
    # TODO: np.asarray, @, np.linalg.norm, then return float(...)
    ...


if __name__ == "__main__":
    print(dot([1, 2, 3], [4, 5, 6]))          # want 32.0
    print(norm([3, 4]))                       # want 5.0
    print(cosine_similarity([1, 2], [2, 4]))  # want 1.0
    print(cosine_similarity([0, 0], [1, 1]))  # want 0.0
