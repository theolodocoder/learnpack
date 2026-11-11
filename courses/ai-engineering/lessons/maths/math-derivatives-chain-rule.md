# Derivatives, gradients and the chain rule

## Why this matters

Training a model means asking one question millions of times: "if I nudge this weight a little, does the loss go up or down, and by how much?" The answer is a derivative. A model with a billion weights needs a billion of them at every step, collected into a vector called the gradient, and the chain rule is how they're computed efficiently. You won't compute these by hand at work (PyTorch does it), but without the intuition, words like "vanishing gradients", "learning rate" and "loss went to nan" stay mysterious.

## The derivative is sensitivity

Forget limits and epsilon-delta proofs for a moment. The derivative of `f` at `x` answers: **if I change the input by a tiny amount, how much does the output change, per unit of input change?**

```
f'(x) ≈ (f(x + h) − f(x)) / h      for a tiny h
```

Take `f(x) = x²` at `x = 3`. Nudge the input from 3 to 3.001: the output goes from 9 to 9.006001. The output moved about 6 times as much as the input did. So `f'(3) ≈ 6`.

```python
f = lambda x: x ** 2
x, h = 3.0, 0.001
print((f(x + h) - f(x)) / h)   # 6.000999999999479  (close to 6)
```

On a graph, that ratio is the **slope** of the curve at that point: the slope of the straight line you'd see if you zoomed in on the curve until it looked flat. Three readings of the same number:

- **Positive derivative:** increasing the input increases the output.
- **Negative derivative:** increasing the input decreases the output.
- **Zero derivative:** at that point, small changes do nothing (a flat spot, such as the bottom of a valley).

For training, the third case is what we're looking for: the bottom of the loss valley.

## A few derivatives worth knowing

You'll meet a handful of functions over and over. Their derivatives, written as rules:

```
f(x) = c         →  f'(x) = 0         a constant doesn't change
f(x) = a·x       →  f'(x) = a         a line has the same slope everywhere
f(x) = x²        →  f'(x) = 2x
f(x) = xⁿ        →  f'(x) = n·xⁿ⁻¹
f(x) = eˣ        →  f'(x) = eˣ
f(x) = ln x      →  f'(x) = 1/x
sigmoid(x) = 1/(1 + e⁻ˣ)  →  sigmoid'(x) = sigmoid(x)·(1 − sigmoid(x))
relu(x) = max(0, x)       →  relu'(x) = 1 if x > 0 else 0
```

And sums split: the derivative of `f(x) + g(x)` is `f'(x) + g'(x)`. That one matters because a loss is usually an average over many examples, so its derivative is the average of their derivatives.

## Numerical derivatives: let the computer nudge

The formula above, `(f(x + h) − f(x)) / h`, is called a **forward difference**. A better version nudges in both directions and is called a **central difference**:

```
f'(x) ≈ (f(x + h) − f(x − h)) / (2h)
```

It's far more accurate for the same `h`: its error shrinks like `h²` instead of `h`.

```python
import math

def numerical_derivative(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)

print(numerical_derivative(lambda x: x ** 2, 3.0))   # 6.000000000039306
print(numerical_derivative(math.sin, 0.0))           # 0.9999999999833332  (cos 0 = 1)
print(numerical_derivative(math.exp, 1.0))           # 2.718281828517632   (e¹ = e)
```

Why not make `h` as small as possible? Floating-point numbers carry about 16 significant digits. With `h = 1e-15`, `f(x + h) − f(x − h)` subtracts two nearly equal numbers and most of the digits cancel, leaving noise. Somewhere around `1e-5` to `1e-6` is the sweet spot for 64-bit floats.

```python
f = lambda x: x ** 2
for h in [1e-1, 1e-5, 1e-10, 1e-14]:
    print(h, (f(3 + h) - f(3 - h)) / (2 * h))
# 0.1 6.000000000000005
# 1e-05 6.000000000039306
# 1e-10 6.000000496442226
# 1e-14 6.128431095930864
```

Numerical derivatives are slow (two function calls per input) but almost impossible to get wrong. That makes them the perfect **checker** for derivatives you work out by hand:

```python
import math

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def sigmoid_prime(x):              # the analytic formula from the table
    s = sigmoid(x)
    return s * (1 - s)

for x in [-2.0, 0.0, 1.5]:
    numeric = (sigmoid(x + 1e-5) - sigmoid(x - 1e-5)) / 2e-5
    print(x, sigmoid_prime(x), numeric, math.isclose(sigmoid_prime(x), numeric, rel_tol=1e-6))
# -2.0 0.1049935854035065 0.10499358540430602 True
# 0.0 0.25 0.2499999999933111 True
# 1.5 0.14914645207033286 0.14914645207197985 True
```

If the two disagree, your formula is wrong. This "gradient check" is how people debugged neural networks before autograd existed, and it's still how autograd libraries are tested.

## Partial derivatives and the gradient

A loss depends on many weights, not one. A **partial derivative** asks the same question for one input at a time, holding all the others fixed. For `f(w₁, w₂) = w₁² + 3·w₂`:

```
∂f/∂w₁ = 2·w₁     (treat w₂ as a constant)
∂f/∂w₂ = 3        (treat w₁ as a constant)
```

The symbol `∂` (curly d) just means "partial": "derivative with respect to this one input, others frozen".

Put all the partial derivatives in a vector and you have the **gradient**, written `∇f`:

```
∇f(w) = [∂f/∂w₁, ∂f/∂w₂, …, ∂f/∂wₙ]
```

The gradient has the same shape as the input. It has a lovely geometric meaning: **it points in the direction in which `f` increases fastest**, and its length says how steep that is. So `−∇f` points straight downhill. That single fact is gradient descent, which is the next lesson.

Computing a gradient numerically is the same nudge, one coordinate at a time:

```python
import numpy as np

def numerical_gradient(f, x, h=1e-5):
    x = np.array(x, dtype=float)
    grad = np.zeros_like(x)
    for i in range(x.size):
        plus, minus = x.copy(), x.copy()
        plus[i] += h
        minus[i] -= h
        grad[i] = (f(plus) - f(minus)) / (2 * h)
    return grad

f = lambda w: w[0] ** 2 + 3 * w[1]
print(numerical_gradient(f, [2.0, 5.0]))           # [4. 3.]   matches [2·w₁, 3]

g = lambda v: np.sum(v ** 2)                          # ‖v‖²
print(numerical_gradient(g, [1.0, -2.0, 0.5]))     # [ 2. -4.  1.]  = 2v
```

Two gradients worth recognising, because they're everywhere:

```
f(x) = w · x      →  ∇ₓf = w          the gradient of a dot product is the other vector
f(x) = ‖x‖²       →  ∇ₓf = 2x
```

> **Note:** A model with `n` weights needs `2n` loss evaluations for a numerical gradient. For a model with a million weights, that's two million forward passes per step. Backpropagation gets all `n` partial derivatives for the cost of about one extra pass. That's why it exists.

## The chain rule

Neural networks are functions inside functions inside functions. The chain rule says how sensitivities combine through that nesting:

```
if y = f(u) and u = g(x), then  dy/dx = dy/du · du/dx
```

Read it as a story about nudges. Nudge `x` a little: `u` moves `du/dx` times as much. Each bit that `u` moves makes `y` move `dy/du` times as much. So the total effect is the product. Sensitivities **multiply** along a chain.

Example: `y = (3x + 1)²`. Let `u = 3x + 1`, so `y = u²`.

```
dy/du = 2u
du/dx = 3
dy/dx = 2u · 3 = 6(3x + 1)
```

At `x = 1`: `6 · 4 = 24`. Check it:

```python
x, h = 1.0, 1e-5
f = lambda x: (3 * x + 1) ** 2
print((f(x + h) - f(x - h)) / (2 * h))   # 24.00000000...
print(6 * (3 * x + 1))                   # 24.0
```

Now the example that matters for AI: one neuron with one weight `w`, one input `x`, a sigmoid, and a squared-error loss against a target `y`:

```
z    = w · x
p    = sigmoid(z)
loss = (p − y)²
```

To find how the loss responds to `w`, chain three local derivatives, each of which is easy on its own:

```
dloss/dp = 2(p − y)
dp/dz    = p(1 − p)          (the sigmoid derivative)
dz/dw    = x
dloss/dw = 2(p − y) · p(1 − p) · x
```

```python
import math

def sigmoid(z):
    return 1 / (1 + math.exp(-z))

def loss(w, x, y):
    return (sigmoid(w * x) - y) ** 2

def dloss_dw(w, x, y):
    p = sigmoid(w * x)                    # forward: remember intermediate values
    return 2 * (p - y) * p * (1 - p) * x  # backward: multiply local derivatives

w, x, y = 0.5, 2.0, 1.0
numeric = (loss(w + 1e-6, x, y) - loss(w - 1e-6, x, y)) / 2e-6
print(dloss_dw(w, x, y), numeric)   # both about -0.2115
```

Notice the pattern: first compute forward and keep the intermediate values (`p`), then multiply local derivatives from the loss backwards. That is backpropagation in miniature. *Backpropagation, and what's next* scales it up to a real network.

Notice also what can go wrong. If `z` is large, `p` is close to 1 and `p(1 − p)` is close to 0. Multiply a few factors like that along a deep chain and the gradient shrinks to nothing: the famous **vanishing gradient** problem, and one reason modern networks prefer ReLU, whose derivative is exactly 1 wherever it's active.

> **Try it:** in the code above, set `w = 10.0` and `y = 0.0`. Now `p` is almost exactly 1, so the loss is close to its maximum of 1.0, yet `dloss_dw` is about `8e-9`. That's a saturated sigmoid: the neuron is badly wrong and can barely learn.

## Common mistakes

- **Forward differences with a large `h`.** `(f(x + h) − f(x)) / h` with `h = 0.1` is off in the first decimal place. Use central differences with `h ≈ 1e-5`.
- **`h` too small.** Below about `1e-8`, rounding error dominates. Smaller isn't better.
- **Nudging an integer array.** `np.array([1, 2])` has an integer dtype; `x[0] += 1e-5` silently stores `1`. Convert with `np.array(x, dtype=float)` first.
- **Modifying the caller's array.** When you nudge `x[i]`, work on a copy or restore it afterwards, or the next coordinate is computed at the wrong point.
- **Dropping a factor in the chain.** Forgetting the inner derivative (the `3` in `(3x + 1)²`, the `x` in `w · x`) is the classic hand-derivation bug. A numerical check catches it instantly.

## Recap

- The derivative is sensitivity: how much the output moves per unit nudge of the input. On a graph, it's the slope.
- Numerical derivative: `(f(x + h) − f(x − h)) / (2h)` with `h ≈ 1e-5`. Slow, reliable, perfect for checking.
- Partial derivatives freeze all inputs but one. The gradient collects them; it points uphill, so `−∇f` points downhill.
- Chain rule: sensitivities multiply along a chain of functions. Compute forward, keep intermediates, multiply local derivatives backwards.
- Long chains of small factors cause vanishing gradients; that's why activation choice matters.
