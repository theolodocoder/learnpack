# Backpropagation by hand

Compute the loss **and every gradient** of a tiny network with one hidden layer, by applying the chain rule backwards. No autograd, just NumPy.

The network and its loss (a regression network, so no softmax):

```
a    = X @ W1 + b1          (n, hidden)    pre-activation
h    = relu(a)              (n, hidden)
pred = h @ W2 + b2          (n, out)
loss = mean((pred − y)²)    one number, averaged over every entry of pred
```

```python
def loss_and_grads(X, y, W1, b1, W2, b2) -> tuple[float, dict]: ...
```

Return `(loss, grads)` where `grads` is a dict with keys `"W1"`, `"b1"`, `"W2"`, `"b2"`, each an array with the **same shape as that parameter**.

The backward pass, one line per step (write `d_name` for `∂loss/∂name`):

```
d_pred = 2 · (pred − y) / pred.size        (n, out)
d_W2   = h.T @ d_pred                      (hidden, out)
d_b2   = d_pred.sum(axis=0)                (out,)
d_h    = d_pred @ W2.T                     (n, hidden)
d_a    = d_h · (a > 0)                     (n, hidden)   relu passes gradient only where it was "on"
d_W1   = X.T @ d_a                         (d, hidden)
d_b1   = d_a.sum(axis=0)                   (hidden,)
```

The tests check every gradient against a numerical estimate, so you'll know immediately if a step is wrong.

## Example

```python
X  = np.array([[1.0, 2.0]]);  y = np.array([[1.0]])
W1 = np.array([[1.0, -1.0], [0.5, 1.0]]);  b1 = np.array([0.0, 0.0])
W2 = np.array([[1.0], [1.0]]);              b2 = np.array([0.0])
loss, g = loss_and_grads(X, y, W1, b1, W2, b2)
# a = [[2, 1]], h = [[2, 1]], pred = [[3]], loss = 4.0
# g["W2"] = [[8], [4]], g["b2"] = [4], g["W1"] = [[4, 4], [8, 8]], g["b1"] = [4, 4]
```
