# Numerical derivatives and gradients

You can estimate any derivative without doing calculus: nudge the input a tiny bit and see how much the output moves.

```python
def numerical_derivative(f, x: float, h: float = 1e-5) -> float: ...
def numerical_gradient(f, x, h: float = 1e-5) -> np.ndarray: ...
```

- `numerical_derivative(f, x, h)`: use the **central difference**

  ```
  f'(x) ≈ (f(x + h) − f(x − h)) / (2h)
  ```

  Return a plain `float`.
- `numerical_gradient(f, x, h)`: `f` takes a NumPy array and returns a single number. Return an array with the same shape as `x` whose entry `i` is `∂f/∂xᵢ`, estimated by nudging **only** `x[i]` up and down by `h`.
  - Work on copies: the caller's `x` must be unchanged afterwards.
  - Convert `x` to a float array first (`np.array(x, dtype=float)`), or nudging an integer array by `1e-5` silently does nothing.

## Example

```python
numerical_derivative(lambda x: x ** 2, 3.0)               # ≈ 6.0
numerical_gradient(lambda v: np.sum(v ** 2), [1.0, -2.0])  # ≈ [2., -4.]
```
