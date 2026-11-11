# Project: tiny semantic search and a tiny network, from scratch

This is the section project. Two small systems, each built only from what you wrote in this section: vectors, cosine similarity, matrix multiplies, gradients and gradient descent.

## Part 1: semantic search

```python
def build_index(doc_vectors) -> np.ndarray: ...
def search(index, query, k: int) -> list[tuple[int, float]]: ...
```

- `build_index(doc_vectors)`: `(n, d)` embeddings in, an `(n, d)` array out with every row normalised to length 1. Zero rows stay zero (no `nan`). This is the "indexing" step real vector databases do once, up front.
- `search(index, query, k)`: return the top `k` results as `(doc_index, score)` pairs, best first, where `score` is the cosine similarity as a plain `float` and `doc_index` a plain `int`.
  - Because the index rows are already unit length, the scores are just `index @ unit_query`.
  - Ties go to the lower index (`np.argsort(-scores, kind="stable")`).
  - `k` larger than the number of docs returns them all; `k <= 0` returns `[]`; a zero query gives every doc a score of `0.0`.

```python
index = build_index([[1, 0, 0], [0.9, 0.1, 0], [0, 0, 1]])
search(index, [1, 0, 0], 2)   # [(0, 1.0), (1, 0.9939)]
```

## Part 2: train a network on XOR

XOR is the classic problem a straight line can't solve: inputs `[0,0]`, `[0,1]`, `[1,0]`, `[1,1]` → targets `0, 1, 1, 0`. One hidden layer fixes that.

```python
def predict(params: dict, X) -> np.ndarray: ...
def train(X, y, hidden=16, lr=0.1, steps=2000, seed=0) -> tuple[dict, list[float]]: ...
```

- `init_params` is written for you in the starter. Use it as is so your run matches the tests.
- `predict(params, X)`: `relu(X @ W1 + b1) @ W2 + b2`. Shape `(n, out)`. No softmax: this is regression on the targets.
- `train(X, y, hidden, lr, steps, seed)`:
  1. `params = init_params(X.shape[1], hidden, y.shape[1], seed)`
  2. Repeat `steps` times: forward pass, record the MSE loss (as a `float`) **before** updating, backward pass (exactly as in *Backpropagation by hand*), then `param -= lr * grad` for all four.
  3. Return `(params, losses)`, with `len(losses) == steps`.

```python
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
y = np.array([[0], [1], [1], [0]], dtype=float)
params, losses = train(X, y)
losses[0], losses[-1]          # about 0.42 → below 0.001
predict(params, X).round(2)    # about [[0], [1], [1], [0]]
```

Check is offline and fast: the whole test file trains a few small networks in well under a second.
