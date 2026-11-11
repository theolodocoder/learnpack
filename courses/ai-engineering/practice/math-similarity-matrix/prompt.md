# A whole batch of similarity scores in one multiply

Search systems rarely score one query at a time. Write a function that scores **every query against every document** with a single matrix multiplication.

```python
def normalize_rows(M) -> np.ndarray: ...
def similarity_matrix(queries, docs) -> np.ndarray: ...
```

- `normalize_rows(M)`: divide each row of a 2-D array by its length so every row has length 1. A row that is all zeros stays all zeros (no division by zero, no `nan`). Return a new float array; don't change the input.
- `similarity_matrix(queries, docs)`: `queries` has shape `(q, d)`, `docs` has shape `(n, d)`. Return an array of shape `(q, n)` where entry `[i, j]` is the cosine similarity of query `i` and document `j`.
  - Use `normalize_rows` on both, then **one** `@`. No Python loops.

Hint for the zero rows: `lengths = np.linalg.norm(M, axis=1, keepdims=True)` has shape `(rows, 1)`, which broadcasts against `M`. `np.divide(M, lengths, out=np.zeros_like(M), where=lengths > 0)` skips the zero rows.

## Example

```python
Q = [[1, 0], [0, 1]]
D = [[2, 0], [1, 1], [0, 0]]
similarity_matrix(Q, D)
# [[1.     , 0.7071, 0.],
#  [0.     , 0.7071, 0.]]
```
