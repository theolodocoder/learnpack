import numpy as np


def rotation_matrix(degrees: float) -> np.ndarray:
    """2x2 matrix that rotates a vector anticlockwise by `degrees`."""
    # TODO: theta = np.radians(degrees); build the matrix with np.cos and np.sin
    ...


def rotate(points, degrees: float) -> np.ndarray:
    """Rotate every row of an (n, 2) array of points. Returns a new (n, 2) array."""
    # TODO: points @ rotation_matrix(degrees).T
    ...


if __name__ == "__main__":
    print(rotation_matrix(90))
    print(rotate([[1, 0], [0, 2]], 90))  # want about [[0, 1], [-2, 0]]
