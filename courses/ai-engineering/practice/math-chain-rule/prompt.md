# The chain rule on a one-weight "network"

A single neuron with one weight `w` sees one input `x` and should output a target `y`:

```
z    = w · x
p    = sigmoid(z) = 1 / (1 + e^(−z))
loss = (p − y)²
```

Write the derivative of the loss with respect to `w` **by hand, using the chain rule**:

```
dloss/dw = dloss/dp · dp/dz · dz/dw
```

with

```
dloss/dp = 2(p − y)
dp/dz    = sigmoid(z) · (1 − sigmoid(z))
dz/dw    = x
```

```python
def sigmoid(z: float) -> float: ...
def loss(w: float, x: float, y: float) -> float: ...
def dloss_dw(w: float, x: float, y: float) -> float: ...
```

Use `math.exp`. Each function returns a `float`. The tests check `dloss_dw` against a numerical derivative of your `loss`, so both must be right.

## Example

```python
sigmoid(0.0)              # 0.5
loss(0.0, 2.0, 1.0)       # 0.25          (p = 0.5, (0.5 - 1)² = 0.25)
dloss_dw(0.0, 2.0, 1.0)   # -0.5          (2·(-0.5) · 0.25 · 2)
```
