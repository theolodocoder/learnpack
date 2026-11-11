import numpy as np


def rotation_matrix(degrees: float) -> np.ndarray:
    """2x2 matrix that rotates a vector anticlockwise by `degrees`."""
    t = np.radians(degrees)
    return np.array([[np.cos(t), -np.sin(t)],
                     [np.sin(t), np.cos(t)]])


def rotate(points, degrees: float) -> np.ndarray:
    """Rotate every row of an (n, 2) array of points. Returns a new (n, 2) array."""
    return np.asarray(points, dtype=float) @ rotation_matrix(degrees).T


if __name__ == "__main__":
    print(rotation_matrix(90))
    print(rotate([[1, 0], [0, 2]], 90))  # want about [[0, 1], [-2, 0]]
