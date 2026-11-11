# Gradient descent: how models learn

## Why this matters

"Training a model" sounds grand, but at its heart it's a short loop: measure how wrong the model is, work out which way to nudge each weight to make it less wrong, take a small step, repeat. That loop, gradient descent, trained every model you'll call through an API, from embedding models to Claude. Fine-tuning is the same loop run again on your data. When someone says a run "diverged" or "the learning rate was too high", this lesson is what they mean.

## Step 1: a model with parameters

Start with the smallest possible model: a straight line.

```
pred = w · x + b
```

`x` is the input, `pred` is the model's guess, and `w` (weight, the slope) and `b` (bias, the intercept) are the **parameters**: the numbers we get to choose. A large language model is the same idea with billions of parameters instead of two.

Say we have data that roughly follows a line, and we want to find the `w` and `b` that fit it best:

```python
import numpy as np

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])   # roughly y = 2x + 1

w, b = 0.0, 0.0                             # a terrible first guess
print(w * xs + b)                           # [0. 0. 0. 0. 0.]
```

## Step 2: a loss function says how wrong we are

To improve, we need a single number that measures "how wrong". That's the **loss**. For predicting numbers, the standard choice is the **mean squared error** (MSE):

```
MSE = mean((pred − y)²) = (1/n) · Σ (predᵢ − yᵢ)²
```

Why squared? Squaring makes every error positive (so overshoots and undershoots don't cancel), punishes big errors much more than small ones, and gives a smooth bowl-shaped function that's easy to take derivatives of.

```python
import numpy as np

def mse(pred, y):
    return float(np.mean((pred - y) ** 2))

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])

print(mse(0.0 * xs + 0.0, ys))   # 33.142  terrible
print(mse(2.0 * xs + 1.0, ys))   # 0.022   very good
```

Now the goal is precise: **find the `w` and `b` that make the loss as small as possible.** Think of the loss as a landscape: for every pair `(w, b)` there's a height (the loss). We're standing somewhere on it, and we want to walk to the bottom of the valley.

> **Note:** Other tasks use other losses. Classification (including predicting the next token) uses **cross-entropy**, which you'll meet in *Neural networks: neurons to next-token probabilities*. The training loop is identical; only the formula for "how wrong" changes.

## Step 3: the gradient points uphill

From the previous lesson: the gradient of the loss with respect to the parameters points in the direction in which the loss **increases** fastest. So to go downhill, step in the **opposite** direction.

For the line and MSE, the partial derivatives come straight from the chain rule. With `errorᵢ = (w·xᵢ + b) − yᵢ`:

```
L     = mean(error²)
∂L/∂w = mean(2 · error · x)      (chain rule: d(error²)/d(error) = 2·error, d(error)/dw = x)
∂L/∂b = mean(2 · error)          (d(error)/db = 1)
```

Read them as intuition, too. If the predictions are too high (`error > 0`), `∂L/∂b` is positive, so stepping against it lowers `b`. The `x` in `∂L/∂w` means points with large inputs have more say about the slope, which makes sense: the slope matters most far from zero.

```python
import numpy as np

def mse_gradients(w, b, xs, ys):
    error = w * xs + b - ys
    return float(np.mean(2 * error * xs)), float(np.mean(2 * error))

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])
print(mse_gradients(0.0, 0.0, xs, ys))   # (-28.04, -10.04)  both negative: increase w and b
```

Always check hand-derived gradients numerically once. It takes three lines:

```python
import numpy as np

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])
L = lambda w, b: np.mean((w * xs + b - ys) ** 2)
h = 1e-6
print((L(h, 0) - L(-h, 0)) / (2 * h), (L(0, h) - L(0, -h)) / (2 * h))   # about -28.04 -10.04
```

## Step 4: take a small step

The update rule of gradient descent, for every parameter `θ`:

```
θ ← θ − lr · ∂L/∂θ
```

`lr` is the **learning rate**: how big a step to take. One step on our data:

```python
import numpy as np

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])

def mse(w, b):
    return float(np.mean((w * xs + b - ys) ** 2))

def gradient_step(w, b, lr):
    error = w * xs + b - ys
    dw, db = np.mean(2 * error * xs), np.mean(2 * error)
    return w - lr * dw, b - lr * db

w, b = 0.0, 0.0
print(mse(w, b))                    # 33.142
w, b = gradient_step(w, b, lr=0.01)
print(round(w, 4), round(b, 4), round(mse(w, b), 3))   # 0.2804 0.1004 24.866
```

One step and the loss dropped by a quarter. Now just repeat.

## Step 5: repeat, and that's training

```python
import numpy as np

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])

def fit_line(xs, ys, lr=0.01, steps=1000):
    w, b = 0.0, 0.0
    for step in range(steps):
        error = w * xs + b - ys
        w -= lr * np.mean(2 * error * xs)
        b -= lr * np.mean(2 * error)
        if step % 250 == 0:
            print(f"step {step:4d}  loss {np.mean(error ** 2):.4f}")
    return w, b

w, b = fit_line(xs, ys, lr=0.05, steps=1000)
print(round(w, 3), round(b, 3))
print(np.polyfit(xs, ys, 1).round(3))   # NumPy's exact least-squares answer, for comparison
# step    0  loss 33.1420
# step  250  loss 0.0214
# step  500  loss 0.0214
# step  750  loss 0.0214
# 1.99 1.04
# [1.99 1.04]
```

The loss falls quickly at first, then slowly as the valley flattens out near the bottom, and the result matches the exact answer from `np.polyfit`. You just trained a model.

That's all "training" is, at any scale:

| Our line | A large language model |
|---|---|
| 2 parameters | billions of parameters |
| `pred = w·x + b` | a transformer, `pred` = probabilities for the next token |
| MSE | cross-entropy on the next token |
| exact gradient over 5 points | gradient on a small random **batch** of text (stochastic gradient descent) |
| `w -= lr * dw` | Adam, a smarter step rule that adapts the step size per parameter |
| gradients by hand | gradients by backpropagation (automatic) |

Every row is a refinement; none changes the core loop.

## The learning rate: too small, too big, just right

The learning rate is the most important knob in training. On our data:

```python
import numpy as np

xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
ys = np.array([1.1, 2.9, 5.2, 6.8, 9.1])

def final_loss(lr, steps=100):
    w, b = 0.0, 0.0
    for _ in range(steps):
        error = w * xs + b - ys
        w, b = w - lr * np.mean(2 * error * xs), b - lr * np.mean(2 * error)
    return float(np.mean((w * xs + b - ys) ** 2))

for lr in [0.0001, 0.01, 0.05, 0.1, 0.2]:
    print(lr, final_loss(lr))
# 0.0001 25.356409025080342
# 0.01 0.030783763390988338
# 0.05 0.021472561109019902
# 0.1 0.0214001402183954
# 0.2 4.1100452431923043e+46
```

There are three regimes:

- **Too small** (`0.0001`): every step is tiny. After 100 steps the loss has barely moved. Training is stable but painfully slow, and on a real model, expensive.
- **Just right** (`0.01` to `0.1`): the loss falls steadily to its minimum, about `0.0214`. Bigger is faster here, right up to the edge.
- **Too big** (`0.2`, for this data): each step overshoots the bottom of the valley and lands higher up the other side. The next step overshoots further. After 100 steps the loss is about `4 × 10⁴⁶`; a few hundred more and it's `inf`, then `nan`. That's **divergence**.

Picture a ball in a bowl. Small steps roll it gently to the bottom. Steps too large fling it from one wall to the other, higher each time. How large is "too large" depends on how steep the bowl is, which depends on the data: inputs with large values give steep losses. That's one reason real pipelines **normalise inputs** (scale them to roughly mean 0, standard deviation 1) before training.

> **Try it:** in the practice editor, run `fit_line` with `lr=0.2` and print the loss every step for the first 20 steps. Watch it grow. Then halve the learning rate and run again.

## Why not just solve it directly?

For a straight line, there's an exact formula (least squares, which `np.polyfit` uses). So why bother with gradient descent? Because for nearly every interesting model there is no formula. A neural network's loss landscape has no closed-form bottom. Gradient descent only needs one thing, the gradient at the current point, and that you can always compute. It's the universal method precisely because it's so dumb: look at the slope where you stand, step downhill, repeat.

It also means it finds *a* low point, not necessarily the lowest. For a line, the MSE landscape is a perfect bowl with one bottom. A neural network's landscape has many valleys. In practice, for large networks, the valleys gradient descent finds are good enough, which is one of the pleasant surprises of deep learning.

## Common mistakes

- **Adding the gradient instead of subtracting it.** `w += lr * dw` climbs uphill. The loss rises every step.
- **Updating `w` and then using the new `w` to compute `b`'s gradient.** Compute all gradients from the same current parameters, then update them all. (In `fit_line` above, both gradients use the same `error`, computed before either update.)
- **Diagnosing divergence as a bug.** If the loss grows or becomes `nan`, lower the learning rate first.
- **Never looking at the loss.** Print or plot the loss over steps. A curve that falls and flattens is healthy; one that's flat from the start means the learning rate is too small or the gradients are wrong.
- **Forgetting the mean.** Using `sum` instead of `mean` in the loss makes the gradient grow with the dataset size, so a learning rate that worked on 5 points diverges on 5,000.

## Recap

- A model has parameters; a loss function (MSE for numbers) turns "how wrong" into one number.
- The gradient of the loss points uphill. Gradient descent steps against it: `θ ← θ − lr · ∂L/∂θ`.
- For a line: `∂L/∂w = mean(2·error·x)`, `∂L/∂b = mean(2·error)`.
- Repeat the step and the loss falls: that loop is training, for a 2-parameter line or a billion-parameter LLM.
- The learning rate trades speed for stability. Too small is slow; too big overshoots and diverges to `nan`.
