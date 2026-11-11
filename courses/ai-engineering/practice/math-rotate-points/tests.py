import numpy as np

from solution import rotate, rotation_matrix


def test_rotation_matrix_columns_are_where_basis_vectors_land():
    R = rotation_matrix(90)
    assert R is not None, "rotation_matrix returned None"
    assert np.shape(R) == (2, 2), f"expected shape (2, 2), got {np.shape(R)}"
    assert np.allclose(R, [[0, -1], [1, 0]]), f"90° matrix should be [[0, -1], [1, 0]], got {R.tolist()}"


def test_rotates_x_axis_to_y_axis():
    got = rotate([[1, 0]], 90)
    assert got is not None, "rotate returned None"
    assert np.allclose(got, [[0, 1]]), f"expected [[0, 1]], got {np.asarray(got).tolist()}"


def test_rotates_many_points_and_keeps_shape():
    pts = [[1, 0], [0, 2], [3, 4]]
    got = rotate(pts, 180)
    assert np.shape(got) == (3, 2), f"expected shape (3, 2), got {np.shape(got)}"
    assert np.allclose(got, [[-1, 0], [0, -2], [-3, -4]]), f"180° should negate every point, got {np.asarray(got).tolist()}"


def test_rotation_preserves_lengths():
    pts = np.array([[3.0, 4.0], [1.0, 1.0], [-2.0, 5.0]])
    got = rotate(pts, 37)
    assert np.allclose(np.linalg.norm(got, axis=1), np.linalg.norm(pts, axis=1)), "a rotation should not change any point's length"


def test_two_rotations_compose_into_one():
    pts = np.array([[1.0, 2.0], [-3.0, 0.5]])
    got = rotate(rotate(pts, 30), 60)
    want = rotate(pts, 90)
    assert np.allclose(got, want), "rotating by 30° then 60° should equal rotating by 90°"
    assert np.allclose(rotation_matrix(60) @ rotation_matrix(30), rotation_matrix(90)), "R(60) @ R(30) should equal R(90)"
