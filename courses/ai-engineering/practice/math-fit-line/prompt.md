# Fit a line by gradient descent

Put the pieces together: start from `w = 0`, `b = 0` and repeat the gradient step until the line fits the data. This loop is training, in miniature.

```python
def fit_line(xs, ys, lr: float = 0.1, steps: int = 1000) -> tuple[float, float]: ...
```

- Model: `pred = w · x + b`. Loss: mean squared error.
- Each step:

  ```
  error = (w·x + b) − y
  w ← w − lr · mean(2 · error · x)
  b ← b − lr · mean(2 · error)
  ```

- Run exactly `steps` steps and return `(w, b)` as plain floats.
- Write the loop yourself with NumPy (don't call `np.polyfit`; the tests use it to check you).

## Example

```python
xs = [0, 1, 2, 3]
ys = [1, 3, 5, 7]          # y = 2x + 1
fit_line(xs, ys, lr=0.05, steps=2000)   # ≈ (2.0, 1.0)
```
