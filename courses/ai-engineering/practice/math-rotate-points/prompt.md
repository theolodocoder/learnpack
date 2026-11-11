# A matrix is a transformation: rotate points

Write a function that rotates 2-D points anticlockwise around the origin by a number of **degrees**, using a rotation matrix.

```python
def rotation_matrix(degrees: float) -> np.ndarray: ...
def rotate(points, degrees: float) -> np.ndarray: ...
```

- `rotation_matrix(degrees)` returns the 2×2 matrix

  ```
  [[cos θ, -sin θ],
   [sin θ,  cos θ]]
  ```

  where `θ` is the angle in radians (`np.radians(degrees)`). Its columns are where the basis vectors `[1, 0]` and `[0, 1]` land.
- `rotate(points, degrees)` takes points of shape `(n, 2)` (one point per row) and returns a new array of shape `(n, 2)`.
  - Each point `p` becomes `R @ p`. For many points stored as rows, that is `points @ R.T`.

## Example

```python
rotate([[1, 0]], 90)          # [[0., 1.]]   (up to tiny float error)
rotate([[1, 0], [0, 2]], 180) # [[-1., 0.], [0., -2.]]
```
