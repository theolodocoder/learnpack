# Gradient checking

When you write gradients by hand (or debug someone else's), the standard sanity check is to compare them with a numerical estimate. Write the checker.

```python
def numerical_grad(f, param, eps: float = 1e-5) -> np.ndarray: ...
def gradient_check(f, param, analytic, eps: float = 1e-5) -> float: ...
```

- `f(param)` takes an array and returns a number (the loss).
- `numerical_grad(f, param, eps)`: for every entry `i` of `param` (any shape), the central difference `(f(p⁺) − f(p⁻)) / (2·eps)` where `p⁺` and `p⁻` are copies of `param` with entry `i` nudged up and down by `eps`. Same shape as `param`. **Don't change `param`.**
- `gradient_check(f, param, analytic, eps)`: compute the numerical gradient and return the **largest relative error** across all entries:

  ```
  rel_err = |analytic − numerical| / max(|analytic| + |numerical|, 1e-12)
  ```

  Return it as a plain `float`. Rule of thumb: below `1e-7` the gradient is right; above `1e-3` it is almost certainly wrong.

## Example

```python
f = lambda p: np.sum(p ** 2)
p = np.array([1.0, -2.0, 3.0])
gradient_check(f, p, 2 * p)   # tiny, around 1e-11
gradient_check(f, p, 3 * p)   # 0.2  (|3p − 2p| / (3|p| + 2|p|) = 1/5)
```
