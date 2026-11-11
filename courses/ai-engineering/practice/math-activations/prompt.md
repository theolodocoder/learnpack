# Activation functions: ReLU, sigmoid and a stable softmax

```python
def relu(x) -> np.ndarray: ...
def sigmoid(x) -> np.ndarray: ...
def softmax(logits) -> np.ndarray: ...
```

- `relu(x)`: `max(0, x)` element-wise. Use `np.maximum`.
- `sigmoid(x)`: `1 / (1 + e^(−x))` element-wise. Use `np.exp`.
- `softmax(logits)`: turn scores into probabilities along the **last axis**:

  ```
  softmax(z)ᵢ = e^(zᵢ) / Σⱼ e^(zⱼ)
  ```

  - It must work on a 1-D array (one set of logits) and on a 2-D array (a batch: one row per example, each row sums to 1).
  - It must be **numerically stable**: `np.exp(1000)` overflows to `inf`, and `inf / inf` is `nan`. Subtract the largest logit in each row first. This doesn't change the answer (the factor `e^(−max)` cancels out) but keeps every exponent ≤ 0.
  - Use `axis=-1, keepdims=True` in `np.max` and `np.sum` so the shapes broadcast.

All three take lists or arrays and return NumPy arrays of the same shape.

## Example

```python
relu([-2, 0, 3])          # [0, 0, 3]
sigmoid([0])              # [0.5]
softmax([1, 2, 3])        # [0.0900, 0.2447, 0.6652]
softmax([1000, 1001])     # [0.2689, 0.7311]   (not nan!)
```
