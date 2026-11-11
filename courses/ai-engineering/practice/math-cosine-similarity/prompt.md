# Dot product, length and cosine similarity

Write three functions. The first two use **plain Python only** (no NumPy) so you see exactly what the maths does. The third uses NumPy.

```python
def dot(a: list[float], b: list[float]) -> float: ...
def norm(a: list[float]) -> float: ...
def cosine_similarity(a, b) -> float: ...
```

- `dot(a, b)`: the sum of the element-wise products, `a₁·b₁ + a₂·b₂ + … + aₙ·bₙ`. If the vectors have different lengths, raise `ValueError`.
- `norm(a)`: the length of the vector, `√(a₁² + a₂² + … + aₙ²)`. Use `math.sqrt`.
- `cosine_similarity(a, b)`: `(a · b) / (‖a‖ · ‖b‖)`, using `np.asarray`, `@` and `np.linalg.norm`. It must return a plain Python `float`.
  - **Zero vector rule:** if either vector has length 0, return `0.0` instead of dividing by zero.

## Example

```python
dot([1, 2, 3], [4, 5, 6])                 # 32.0   (4 + 10 + 18)
norm([3, 4])                              # 5.0
cosine_similarity([1, 0], [0, 1])         # 0.0    (perpendicular)
cosine_similarity([1, 2], [2, 4])         # 1.0    (same direction)
cosine_similarity([0, 0], [1, 1])         # 0.0    (zero vector rule)
```
