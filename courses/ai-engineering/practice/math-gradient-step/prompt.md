# Mean squared error and one gradient-descent step

The model is a straight line: `pred = w · x + b`. Write the loss, its gradients, and one step of gradient descent.

```python
def mse(pred, y) -> float: ...
def mse_gradients(w: float, b: float, xs, ys) -> tuple[float, float]: ...
def gradient_step(w: float, b: float, xs, ys, lr: float) -> tuple[float, float]: ...
```

- `mse(pred, y)`: `mean((pred − y)²)` as a plain `float`.
- `mse_gradients(w, b, xs, ys)`: the partial derivatives of `L = mean((w·x + b − y)²)`:

  ```
  error = (w·x + b) − y          (one per data point)
  ∂L/∂w = mean(2 · error · x)
  ∂L/∂b = mean(2 · error)
  ```

  Return `(dw, db)` as floats.
- `gradient_step(w, b, xs, ys, lr)`: move each parameter a small step **against** its gradient and return the new `(w, b)`:

  ```
  w_new = w − lr · ∂L/∂w
  b_new = b − lr · ∂L/∂b
  ```

Use NumPy arrays (`np.asarray`) so these work on lists and arrays alike. No loops needed.

## Example

```python
xs, ys = [1, 2, 3], [2, 4, 6]       # the true line is y = 2x
mse([2, 4, 6], ys)                   # 0.0
mse_gradients(0.0, 0.0, xs, ys)      # (-18.666..., -8.0)
gradient_step(0.0, 0.0, xs, ys, 0.01)  # (0.18666..., 0.08)
```
