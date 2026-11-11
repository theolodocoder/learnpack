# Backpropagation, and what's next

## Why this matters

Gradient descent needs the gradient of the loss with respect to every weight. Backpropagation is the algorithm that computes all of them in one backward sweep, for roughly the cost of one extra forward pass. Every deep learning framework (PyTorch, JAX, TensorFlow) is, at its core, a machine for doing this automatically. You'll never hand-write it at work, but doing it once for a tiny network makes the frameworks transparent: you'll know what `loss.backward()` computes, why it needs memory for the intermediate values, and what to suspect when gradients come out as zero or `nan`.

## The idea: the chain rule, run backwards

In *Derivatives, gradients and the chain rule* you differentiated a one-weight neuron by multiplying local derivatives from the loss back to the weight:

```
dloss/dw = dloss/dp · dp/dz · dz/dw
```

Backpropagation is exactly this, organised for a whole network:

1. **Forward pass:** compute every intermediate value from input to loss, and *keep them*.
2. **Backward pass:** start at the loss with `dloss/dloss = 1`. Walk back through each operation. At each step, take the gradient flowing in from above ("how much does the loss care about my output?") and multiply by the operation's local derivative to get "how much does the loss care about my inputs?".

The key efficiency: the gradient arriving at a layer is computed once and reused for every weight in that layer and every layer below. Nothing is recomputed.

## The local rules you need

A small network is built from just three operations. Here's how each passes gradients backwards. Write `d_name` to mean `∂loss/∂name`, an array with the same shape as `name`.

**Matrix multiply plus bias:** `out = X @ W + b`, with `X: (n, d_in)`, `W: (d_in, d_out)`, `out: (n, d_out)`.

```
d_W = X.T @ d_out          (d_in, n) @ (n, d_out) → (d_in, d_out)    same shape as W
d_b = d_out.sum(axis=0)    b was added to every row, so its gradient sums over rows
d_X = d_out @ W.T          (n, d_out) @ (d_out, d_in) → (n, d_in)    same shape as X
```

You don't have to memorise these. Derive them from shapes: `d_W` must have `W`'s shape, and the only way to combine `X` and `d_out` into `(d_in, d_out)` is `X.T @ d_out`. Same trick for `d_X`. (It's also what the chain rule gives, entry by entry: `out[i, j] = Σₖ X[i, k] · W[k, j]`, so `∂out[i, j]/∂W[k, j] = X[i, k]`.)

**ReLU:** `h = relu(a)`. The local derivative is 1 where `a > 0` and 0 elsewhere, so the gradient passes through where the unit was active and is blocked where it wasn't:

```
d_a = d_h * (a > 0)
```

**Mean squared error:** `loss = mean((pred − y)²)` over all `N = pred.size` entries:

```
d_pred = 2 · (pred − y) / N
```

## A tiny network, by hand

The network: one hidden ReLU layer, a linear output, and MSE.

```
a    = X @ W1 + b1
h    = relu(a)
pred = h @ W2 + b2
loss = mean((pred − y)²)
```

Backwards, one rule at a time, from the loss to the input:

```
d_pred = 2 · (pred − y) / pred.size
d_W2   = h.T @ d_pred
d_b2   = d_pred.sum(axis=0)
d_h    = d_pred @ W2.T
d_a    = d_h * (a > 0)
d_W1   = X.T @ d_a
d_b1   = d_a.sum(axis=0)
```

Read it top to bottom and you can see the gradient "flowing" back: from the loss into `pred`, through `W2` into `h`, through the ReLU gate into `a`, and into `W1`. Each line uses the one before it. That's the reuse that makes backprop fast.

Let's trace one example by hand so every number is visible: one input `X = [[1, 2]]`, target `y = [[1]]`, two hidden units.

```python
import numpy as np

X  = np.array([[1.0, 2.0]]);  y = np.array([[1.0]])
W1 = np.array([[1.0, -1.0],
               [0.5,  1.0]]);  b1 = np.array([0.0, 0.0])
W2 = np.array([[1.0],
               [1.0]]);        b2 = np.array([0.0])

# forward (keep everything)
a = X @ W1 + b1           # [[2. 1.]]
h = np.maximum(0, a)      # [[2. 1.]]  both units active
pred = h @ W2 + b2        # [[3.]]
loss = np.mean((pred - y) ** 2)
print(loss)               # 4.0      prediction 3, target 1, error 2, squared 4

# backward
d_pred = 2 * (pred - y) / pred.size   # [[4.]]   the loss rises 4 per unit rise in pred
d_W2 = h.T @ d_pred                   # [[8.], [4.]]
d_b2 = d_pred.sum(axis=0)             # [4.]
d_h  = d_pred @ W2.T                  # [[4. 4.]]
d_a  = d_h * (a > 0)                  # [[4. 4.]]  both units were active, so nothing blocked
d_W1 = X.T @ d_a                      # [[4. 4.], [8. 8.]]
d_b1 = d_a.sum(axis=0)                # [4. 4.]
print(d_W2.ravel(), d_W1.tolist())    # [8. 4.] [[4.0, 4.0], [8.0, 8.0]]
```

Sanity-check the intuition. The prediction is too high, so every gradient is positive: increasing any weight would make it even higher. Gradient descent will decrease them all. `d_W2[0]` (8) is twice `d_W2[1]` (4) because hidden unit 0 had twice the activation, so its outgoing weight had twice the effect. Every number has a reason.

## Gradient checking: trust, but verify

Hand-written backward passes are easy to get subtly wrong: a missing transpose that happens to have the right shape, a forgotten ReLU mask, a sum over the wrong axis. The fix is the numerical derivative from the derivatives lesson: nudge each weight, see how the loss moves, and compare.

Compare with a **relative error**, because gradients can be huge or tiny and a fixed tolerance won't suit both:

```
rel_err = |analytic − numerical| / max(|analytic| + |numerical|, tiny)
```

Rules of thumb with 64-bit floats and `eps ≈ 1e-5`: below `1e-7` is correct, around `1e-4` is suspicious, above `1e-2` is a bug.

```python
import numpy as np

def loss_fn(X, y, W1, b1, W2, b2):
    return np.mean((np.maximum(0, X @ W1 + b1) @ W2 + b2 - y) ** 2)

def backprop(X, y, W1, b1, W2, b2):
    a = X @ W1 + b1
    h = np.maximum(0, a)
    pred = h @ W2 + b2
    d_pred = 2 * (pred - y) / pred.size
    d_a = (d_pred @ W2.T) * (a > 0)
    return {"W1": X.T @ d_a, "b1": d_a.sum(axis=0), "W2": h.T @ d_pred, "b2": d_pred.sum(axis=0)}

def numerical_grad(f, param, eps=1e-5):
    grad = np.zeros_like(param)
    for i in np.ndindex(param.shape):
        old = param[i]
        param[i] = old + eps; up = f()
        param[i] = old - eps; down = f()
        param[i] = old                       # always restore!
        grad[i] = (up - down) / (2 * eps)
    return grad

rng = np.random.default_rng(0)
X, y = rng.normal(size=(5, 3)), rng.normal(size=(5, 2))
params = {"W1": rng.normal(size=(3, 4)), "b1": rng.normal(size=4),
          "W2": rng.normal(size=(4, 2)), "b2": rng.normal(size=2)}

analytic = backprop(X, y, **params)
for name, p in params.items():
    num = numerical_grad(lambda: loss_fn(X, y, **params), p)
    rel = np.abs(analytic[name] - num) / np.maximum(np.abs(analytic[name]) + np.abs(num), 1e-12)
    print(f"{name}: max relative error {rel.max():.1e}")
```

All four come out tiny. Now break it on purpose: delete `* (a > 0)` from `backprop` and run again. `W2` and `b2` still pass (they're above the ReLU), but `W1` and `b1` fail loudly. A gradient check doesn't just tell you *that* something is wrong, it tells you *which layer*.

> **Note:** ReLU has a kink at 0, where the derivative isn't defined. If a pre-activation lands within `eps` of 0, the numerical gradient straddles the kink and disagrees with the analytic one. With random inputs this is rare; if one entry fails and the rest pass, that's the likely cause.

## From this to `loss.backward()`

Frameworks generalise what you just did. Every operation (`@`, `+`, `relu`, `exp`, `mean`, and hundreds more) is registered with its local backward rule. During the forward pass the framework records which operations ran on which tensors, forming a graph. `loss.backward()` walks that graph in reverse, applying each rule and adding up gradients where a value was used more than once. That's **automatic differentiation** (autograd).

Two practical consequences you'll now understand:

- **Training uses far more memory than inference.** The backward pass needs the intermediate values (`a`, `h`, …) from the forward pass, so they're all kept. During inference (calling a model through an API), nothing is kept.
- **Dead and vanishing gradients are visible in the equations.** A ReLU unit whose `a` is negative for every input gets `d_a = 0` forever: it never learns again. A chain of sigmoids multiplies many factors below 0.25, so early layers get almost no gradient.

The full loop, which you'll build in the project, is: forward, loss, backward, `param -= lr * grad` for every parameter, repeat. It's the same five lines whether the network has 50 parameters or 50 billion.

## What's next: the path for next year

You don't need more maths to ship LLM products in the next few months: the main track covers what you'll use. But if you want to go deeper into how models work (and many of the best-paid AI roles do), here's the order that works:

1. **Andrej Karpathy, *Neural Networks: Zero to Hero*.** The best next step, by a long way. He builds `micrograd` (a tiny autograd engine, exactly this lesson generalised) in the first video, then works up through language models to a GPT, from an empty file. Code along with every video rather than watching. The playlist is linked in this lesson's videos.
2. **Probability and statistics.** Distributions, expectation, variance, Bayes' rule, maximum likelihood. Cross-entropy, sampling, evaluation metrics and A/B tests all live here, and you'll use them constantly when you build evals.
3. **PyTorch.** Once you've built autograd by hand, PyTorch is just a fast, GPU-backed version of what you wrote. Rebuild this section's network in PyTorch and compare: `torch.nn.Linear` is `X @ W + b`, `loss.backward()` is your backward pass, `torch.optim.SGD` is `param -= lr * grad`.
4. **Then, the transformer.** With all of the above, 3Blue1Brown's transformer videos and Karpathy's "Let's build GPT" become fully understandable rather than impressive.

## Common mistakes

- **Not keeping forward values.** The backward pass needs `a`, `h` and the inputs. Recomputing them is wasteful; overwriting them gives wrong gradients.
- **Forgetting the ReLU mask.** Without `* (a > 0)`, gradients flow through units that were switched off.
- **Summing biases over the wrong axis.** A bias added to every row gets `d_out.sum(axis=0)`, which has the bias's shape. If your gradient's shape doesn't match its parameter's shape, it's wrong.
- **Forgetting the `1/N` from the mean.** Gradients come out `N` times too big, and a learning rate that should work diverges.
- **Not restoring a nudged weight in a gradient check.** Every later check is then computed at the wrong point. Copy, or restore in the same loop.

## Recap

- Backpropagation is the chain rule applied from the loss backwards, reusing each layer's incoming gradient for everything below it.
- Three local rules cover a basic network: `X @ W + b` (`d_W = X.T @ d_out`, `d_b = d_out.sum(0)`, `d_X = d_out @ W.T`), ReLU (`d_a = d_h * (a > 0)`), MSE (`d_pred = 2(pred − y)/N`).
- Every gradient has the same shape as its parameter; use that to derive and check formulas.
- Check hand-written gradients numerically with a relative error. Below `1e-7` is right.
- Frameworks automate exactly this. Next: Karpathy's *Zero to Hero*, then probability and statistics, then PyTorch.
