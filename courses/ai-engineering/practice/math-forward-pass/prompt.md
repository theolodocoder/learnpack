# A forward pass through a two-layer network

Write the forward pass of a small classifier:

```
h      = relu(x @ W1 + b1)       hidden layer
logits = h @ W2 + b2             output scores, one per class
probs  = softmax(logits)         probabilities, one per class
```

```python
def forward(x, W1, b1, W2, b2) -> np.ndarray: ...
```

- Shapes: `x` is `(d,)` for one example or `(n, d)` for a batch; `W1` is `(d, hidden)`, `b1` is `(hidden,)`, `W2` is `(hidden, classes)`, `b2` is `(classes,)`.
- Return `probs`: shape `(classes,)` for one example, `(n, classes)` for a batch. With `@`, broadcasting and `axis=-1` you don't need any `if` for this.
- Write `relu` and a numerically stable `softmax` (along the last axis) in the same file; the starter has stubs. You wrote these in *Activation functions*, so copy them over.

## Example

```python
x  = np.array([1.0, 2.0])
W1 = np.array([[1.0, -1.0], [0.5, 1.0]])
b1 = np.array([0.0, -2.0])
W2 = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 1.0]])
b2 = np.zeros(3)
forward(x, W1, b1, W2, b2)
# h = relu([2.0, -1.0]) = [2.0, 0.0]; logits = [2.0, 0.0, -2.0]
# ≈ [0.8668, 0.1173, 0.0159]
```
