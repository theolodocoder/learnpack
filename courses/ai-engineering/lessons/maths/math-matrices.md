# Matrices: transformations, shapes and batch similarity

## Why this matters

Almost every number-crunching step in an AI system is a matrix multiplication. A neural network layer is one. Scoring 10 queries against 100,000 document embeddings is one. Attention inside a transformer is a few of them. If you can read a line like `scores = Q @ D.T` and immediately know what shape comes out and what each entry means, you can read real ML code, debug shape errors in seconds, and write search code that is hundreds of times faster than a Python loop.

## A matrix is a grid of numbers

A matrix is a rectangular grid of numbers with some number of rows and columns. Its **shape** is `(rows, columns)`. In NumPy it's a 2-D array:

```python
import numpy as np

M = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 6.0]])
print(M.shape)    # (2, 3): 2 rows, 3 columns
print(M[0])       # [1. 2. 3.]  row 0
print(M[:, 1])    # [2. 5.]     column 1
print(M.T)        # the transpose: rows become columns, shape (3, 2)
```

In AI code a matrix usually means one of two things:

1. **A stack of vectors.** An embeddings matrix with shape `(n_docs, dim)` holds one embedding per row. A batch of inputs with shape `(batch, features)` holds one example per row.
2. **A transformation.** The weights of a neural network layer: a machine that turns one vector into another.

The second view is the deep one, so let's build it.

## A matrix is a linear transformation

Think of a 2×2 matrix as a function that moves every point in the plane. The rule that makes it a matrix (a *linear* transformation) is: grid lines stay straight, parallel and evenly spaced, and the origin stays put. Rotations, stretches, shears and reflections all qualify.

Here's the key fact: **the columns of the matrix are where the basis vectors land.** The basis vectors are `î = [1, 0]` and `ĵ = [0, 1]`. Every vector is a combination of them: `[x, y] = x·î + y·ĵ`. Because the transformation is linear, the result is the same combination of wherever `î` and `ĵ` landed:

```
A @ [x, y] = x · (first column of A) + y · (second column of A)
```

```python
import numpy as np

A = np.array([[2.0, 0.0],
              [0.0, 3.0]])       # stretch x by 2, y by 3
v = np.array([1.0, 1.0])
print(A @ v)                      # [2. 3.]
print(1.0 * A[:, 0] + 1.0 * A[:, 1])   # [2. 3.]  same thing, built from the columns
```

A rotation by angle `θ` sends `î` to `[cos θ, sin θ]` and `ĵ` to `[−sin θ, cos θ]`. Put those in as columns and you have the rotation matrix:

```
R(θ) = [[cos θ, −sin θ],
        [sin θ,  cos θ]]
```

```python
import numpy as np

t = np.radians(90)
R = np.array([[np.cos(t), -np.sin(t)],
              [np.sin(t),  np.cos(t)]])
print((R @ np.array([1.0, 0.0])).round(6))   # [0. 1.]   x-axis rotated onto y-axis
print((R @ np.array([3.0, 4.0])).round(6))   # [-4.  3.]
```

Why care, as an AI engineer? Because a neural network layer `W @ x` is exactly this: it reshapes the space its inputs live in. Training is the search for the matrices whose reshaping makes the problem easy (for example, so that cats and dogs end up on opposite sides of a line).

## Matrix–vector multiplication, row by row

The columns picture tells you what a matrix *does*. To compute the result, use the rows: entry `i` of `A @ v` is the **dot product of row `i` of `A` with `v`**.

```
A has shape (m, n), v has shape (n,)  →  A @ v has shape (m,)
(A @ v)ᵢ = Aᵢ · v
```

```python
import numpy as np

A = np.array([[1.0, 2.0, 3.0],
              [4.0, 5.0, 6.0]])   # (2, 3)
v = np.array([1.0, 0.0, -1.0])     # (3,)
print(A @ v)                        # [-2. -2.]
print([float(row @ v) for row in A])  # [-2.0, -2.0]  the same two dot products, by hand
```

Read that again with embeddings in mind. If `A` is a matrix of document embeddings (one per row) and `v` is a query embedding, then `A @ v` is **every document's dot product with the query, in one operation**. That's the line from the previous lesson, `doc_vecs @ query`, explained.

The number of columns of `A` must equal the length of `v`: each row is dotted with `v`, and the dot product needs equal lengths. A mismatch is the most common error you'll hit:

```python
import numpy as np

A = np.ones((2, 3))
try:
    A @ np.ones(2)
except ValueError as e:
    print(e)   # matmul: Input operand 1 has a mismatch in its core dimension 0 ...
```

## Matrix–matrix multiplication

Multiplying two matrices is just doing matrix–vector multiplication for every column of the second one. The shape rule is the one to memorise:

```
(m, n) @ (n, p)  →  (m, p)
       inner dims must match; outer dims survive
(A @ B)ᵢⱼ = row i of A · column j of B
```

```python
import numpy as np

A = np.array([[1.0, 2.0],
              [3.0, 4.0],
              [5.0, 6.0]])     # (3, 2)
B = np.array([[1.0, 0.0, 2.0, -1.0],
              [0.0, 1.0, 1.0,  1.0]])   # (2, 4)
C = A @ B
print(C.shape)                  # (3, 4)
print(C[2, 3], A[2] @ B[:, 3])  # 1.0 1.0   entry (2, 3) is row 2 of A · column 3 of B
```

Geometrically, `A @ B` is the transformation "first apply `B`, then apply `A`". It reads right to left, like function composition `f(g(x))`. Order matters: in general `A @ B` is not `B @ A`.

```python
import numpy as np

def rot(deg):
    t = np.radians(deg)
    return np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])

stretch = np.array([[2.0, 0.0], [0.0, 1.0]])
print(np.allclose(rot(30) @ rot(60), rot(90)))         # True: two rotations compose into one
print(np.allclose(stretch @ rot(90), rot(90) @ stretch))  # False: order matters
```

This is also why a stack of neural network layers needs something non-linear between them. Two matrix multiplies in a row, `W2 @ (W1 @ x)`, are the same as one matrix `(W2 @ W1) @ x`. Without an activation function in between, depth buys nothing. You'll see this in *Neural networks: neurons to next-token probabilities*.

> **Try it:** make a random `(3, 4)` matrix and a random `(4, 5)` matrix with `np.random.default_rng(0).normal(size=...)`, multiply them, and predict the shape before you print it. Then try them the other way round and read the error.

## Shapes, the transpose, and points stored as rows

Data in ML code is almost always stored **one example per row**: shape `(n, d)`. But the maths above writes vectors as columns being multiplied from the left, `A @ v`. To apply a transformation `A` to every row of a data matrix `X` at once, transpose:

```
apply A to each row of X:   X @ A.T     (n, d) @ (d, d) → (n, d)
```

```python
import numpy as np

t = np.radians(90)
R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
points = np.array([[1.0, 0.0],
                   [0.0, 2.0],
                   [3.0, 4.0]])          # three points, one per row
print((points @ R.T).round(6))
# [[ 0.  1.]
#  [-2.  0.]
#  [-4.  3.]]
```

Neural network libraries usually store weights the other way round so that no transpose is needed: a layer is `X @ W + b` with `W` of shape `(in_features, out_features)`. Same maths, different bookkeeping. When you read code, check the shapes rather than assuming a convention.

## Broadcasting

Look at that `+ b`. `X @ W` has shape `(n, out)` and `b` has shape `(out,)`. NumPy adds `b` to **every row** automatically. That's **broadcasting**: when shapes differ, NumPy lines them up from the right and stretches any dimension of size 1 (or a missing dimension) to match.

```
(n, out) + (out,)      → (n, out)    b added to every row
(n, d)   / (n, 1)      → (n, d)      each row divided by its own number
(n, d)   / (n,)        → error, unless n == d (and then it's silently wrong!)
```

```python
import numpy as np

X = np.array([[3.0, 4.0],
              [1.0, 0.0],
              [0.0, 2.0]])
lengths = np.linalg.norm(X, axis=1, keepdims=True)   # shape (3, 1), not (3,)
print(lengths.shape)        # (3, 1)
print(X / lengths)          # every row now has length 1
# [[0.6 0.8]
#  [1.  0. ]
#  [0.  1. ]]
```

`keepdims=True` is the trick: it keeps the reduced axis as size 1, so `(3, 1)` broadcasts against `(3, 2)` row by row. Without it you get shape `(3,)`, which NumPy tries to line up with the *columns*, and you'd get either an error or, for a square matrix, a silently wrong answer.

## A whole batch of similarities is one matrix multiply

Now put it together. You have `q` query embeddings, shape `(q, d)`, and `n` document embeddings, shape `(n, d)`. You want every query's cosine similarity with every document: a `(q, n)` table.

1. Normalise every row of both matrices to length 1 (broadcasting with `keepdims=True`).
2. Multiply: `(q, d) @ (d, n) → (q, n)`. Entry `[i, j]` is row `i` of the queries dotted with column `j` of `D.T`, which is row `j` of `D`. Because both are unit length, that dot product *is* the cosine similarity.

```python
import numpy as np

rng = np.random.default_rng(0)
Q = rng.normal(size=(3, 8))      # 3 queries, 8-dimensional embeddings
D = rng.normal(size=(5, 8))      # 5 documents

Qn = Q / np.linalg.norm(Q, axis=1, keepdims=True)
Dn = D / np.linalg.norm(D, axis=1, keepdims=True)
S = Qn @ Dn.T
print(S.shape)                   # (3, 5)

# Check one entry against the one-at-a-time formula
i, j = 2, 4
print(np.isclose(S[i, j], Q[i] @ D[j] / (np.linalg.norm(Q[i]) * np.linalg.norm(D[j]))))  # True

best = np.argmax(S, axis=1)      # best document for each query
print(best.shape)                # (3,)
```

This is not just tidier than two nested loops. NumPy hands the multiply to optimised BLAS routines that use every core and SIMD instruction available; on a laptop, `(100, 768) @ (768, 100_000)` takes a fraction of a second, while the equivalent Python loop takes minutes. Vector databases, GPUs and the attention mechanism in transformers (`Q @ K.T`, the same pattern) are all built on this.

## Common mistakes

- **Shape mismatch in `@`.** Write the shapes down: `(m, n) @ (n, p)`. If the inner numbers differ, you probably need a transpose.
- **Forgetting `keepdims=True`.** Dividing `(n, d)` by `(n,)` either fails or, worse, when `n == d`, divides by the wrong thing without any error.
- **Using `*` instead of `@`.** `*` multiplies element by element (with broadcasting). `@` is matrix multiplication. `A * B` on two `(3, 3)` matrices runs fine and gives a completely different answer.
- **Assuming `A @ B == B @ A`.** Order is the order of operations: right one first.
- **Looping in Python over rows.** If you write `for row in X: ... row @ v`, it can almost always be one `X @ v`.

## Recap

- A matrix is a grid of numbers with a shape `(rows, cols)`, and also a linear transformation whose **columns are where the basis vectors land**.
- `A @ v`: each entry is a row of `A` dotted with `v`. With documents as rows, it scores every document against a query at once.
- `(m, n) @ (n, p) → (m, p)`. `A @ B` means "apply `B`, then `A`". Order matters.
- Data is stored one example per row; apply a transformation to all rows with `X @ A.T` (or store weights as `(in, out)` and write `X @ W`).
- Broadcasting stretches size-1 and missing dimensions; `keepdims=True` keeps reductions lined up with rows.
- Batch cosine similarity is: normalise rows, then `Qn @ Dn.T`.
