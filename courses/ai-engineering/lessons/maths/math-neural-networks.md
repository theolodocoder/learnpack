# Neural networks: neurons to next-token probabilities

## Why this matters

Every LLM you call is a neural network whose last step turns a vector of raw scores, called **logits**, into a probability for every token in its vocabulary, then picks one. Embedding models are neural networks whose output is the vector you store. Once you've written a forward pass yourself, phrases like "hidden size 4096", "the logits", "softmax over the vocabulary" and "a classification head" stop being jargon and become shapes you can picture.

## One neuron

A neuron takes a vector of inputs, computes a weighted sum plus a bias, and passes the result through an **activation function**:

```
z = w · x + b          (a dot product plus a number)
a = activation(z)
```

`w` (the weights) and `b` (the bias) are the parameters that training adjusts. The dot product means the neuron "fires" most strongly when the input points in the same direction as its weights, so each neuron is a little pattern detector.

```python
import numpy as np

x = np.array([0.5, -1.0, 2.0])     # 3 input features
w = np.array([1.0, 0.5, 0.25])     # this neuron's weights
b = -0.1
z = w @ x + b
print(z)                            # 0.4
print(max(0.0, z))                  # 0.4  after a ReLU activation
```

## Activation functions

Without an activation, a neuron is just a linear function, and (as you saw in *Matrices: transformations, shapes and batch similarity*) stacking linear functions gives another linear function. The activation adds the bend that lets a network represent curves, corners and decisions. Three you need to know:

**ReLU** (rectified linear unit): `relu(z) = max(0, z)`. Zero for negative inputs, the identity for positive ones. Cheap, and its gradient is exactly 1 wherever it's active, so gradients don't shrink as they pass through. The default choice for hidden layers.

**Sigmoid**: `sigmoid(z) = 1 / (1 + e^(−z))`. Squashes any number into the range 0 to 1, with `sigmoid(0) = 0.5`. Useful as a single probability ("is this spam?"). In hidden layers it has fallen out of favour because it saturates: for large `|z|` its gradient is nearly 0.

**Softmax**: turns a whole vector of scores into a probability distribution, all positive and summing to 1:

```
softmax(z)ᵢ = e^(zᵢ) / Σⱼ e^(zⱼ)
```

Exponentiating makes everything positive and exaggerates differences; dividing by the total makes it sum to 1. The largest score gets the largest probability, but every option keeps some.

```python
import numpy as np

def relu(z):
    return np.maximum(0, z)

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def softmax_naive(z):
    e = np.exp(z)
    return e / e.sum()

z = np.array([-2.0, 0.0, 3.0])
print(relu(z))                   # [0. 0. 3.]
print(sigmoid(z).round(3))       # [0.119 0.5   0.953]
print(softmax_naive(z).round(3)) # [0.006 0.047 0.946]   sums to 1
```

### Making softmax numerically stable

`np.exp(1000)` is larger than the biggest 64-bit float, so it becomes `inf`, and `inf / inf` is `nan`. Real logits can easily be in the hundreds. The fix uses a property of softmax: adding the same constant to every score doesn't change the result (the `e^c` factor cancels top and bottom). So subtract the maximum first. Now the largest exponent is `e⁰ = 1` and nothing overflows.

```python
import numpy as np

def softmax(z):
    z = np.asarray(z, dtype=float)
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)

big = np.array([1000.0, 1001.0, 1002.0])
with np.errstate(over="ignore", invalid="ignore"):
    print(np.exp(big) / np.exp(big).sum())                            # [nan nan nan]
print(softmax(big).round(3))                                          # [0.09  0.245 0.665]
print(softmax([0.0, 1.0, 2.0]).round(3))                              # [0.09  0.245 0.665]  same!

batch = np.array([[1.0, 2.0, 3.0],
                  [5.0, 5.0, 5.0]])
print(softmax(batch).round(3))   # one distribution per row
# [[0.09  0.245 0.665]
#  [0.333 0.333 0.333]]
```

`axis=-1, keepdims=True` makes it work for a single vector and for a batch with one row per example. Every real implementation does the max-subtraction trick.

## A layer is a matrix multiply

A layer is many neurons looking at the same input, each with its own weights. Stack each neuron's weight vector as a **column** of a matrix `W` with shape `(inputs, neurons)` and all the dot products happen at once:

```
h = activation(x @ W + b)
x: (d_in,)   W: (d_in, d_out)   b: (d_out,)   h: (d_out,)
```

And for a whole batch of inputs, one per row, it's the same line:

```
X: (n, d_in)  →  X @ W: (n, d_out)  →  + b broadcasts to every row
```

This is why GPUs matter for AI: a layer applied to a batch is one big matrix multiply, which is exactly what GPUs are built to do fast.

## A network is layers in a row

A two-layer network (one hidden layer) for classifying into `C` classes:

```
h      = relu(x @ W1 + b1)      hidden layer:  (d,)      → (hidden,)
logits = h @ W2 + b2            output layer:  (hidden,) → (C,)
probs  = softmax(logits)        probabilities over the C classes
```

The hidden layer re-describes the input in terms of features it has learned to detect; the output layer combines those features into a score per class. Computing all of this from input to output is the **forward pass**.

```python
import numpy as np

def relu(z):
    return np.maximum(0, z)

def softmax(z):
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)

def forward(x, W1, b1, W2, b2):
    h = relu(x @ W1 + b1)
    logits = h @ W2 + b2
    return softmax(logits)

rng = np.random.default_rng(0)
d, hidden, C = 4, 8, 3
W1, b1 = rng.normal(size=(d, hidden)) * 0.5, np.zeros(hidden)
W2, b2 = rng.normal(size=(hidden, C)) * 0.5, np.zeros(C)

x = np.array([1.0, 0.0, -1.0, 0.5])
print(forward(x, W1, b1, W2, b2).round(3))           # 3 probabilities summing to 1

X = rng.normal(size=(5, d))                           # a batch of 5 examples
print(forward(X, W1, b1, W2, b2).shape)               # (5, 3): one distribution per row
print(W1.size + b1.size + W2.size + b2.size)          # 67 parameters
```

With random weights the probabilities are meaningless. Training (gradient descent on a loss) is what makes them useful. The parameter count is just the size of every weight matrix and bias added up. A "7B" model has about 7 billion.

> **Try it:** change `hidden` to 1,024 and `d` to 768 (a typical embedding size) and print the parameter count. Then imagine dozens of such layers.

## Logits, probabilities and next-token prediction

Here's the connection to the LLMs you'll build with. A language model reads the text so far and, at its last layer, produces one **logit per token in its vocabulary** (tens of thousands of them, sometimes over 100,000). Softmax turns those into a probability distribution over "what token comes next". Then a token is chosen and appended, and the whole thing runs again. That's text generation.

```python
import numpy as np

def softmax(z):
    e = np.exp(z - z.max())
    return e / e.sum()

vocab = ["Lagos", "Abuja", "London", "pizza", "the"]
logits = np.array([4.1, 3.2, 1.0, -2.0, 0.5])         # after "The largest city in Nigeria is"
probs = softmax(logits)
for token, p in sorted(zip(vocab, probs), key=lambda t: -t[1]):
    print(f"{token:7s} {p:.3f}")
# Lagos   0.675
# Abuja   0.274
# London  0.030
# the     0.018
# pizza   0.002

print(vocab[int(np.argmax(probs))])                    # Lagos   (greedy decoding)
rng = np.random.default_rng(42)
print(vocab[rng.choice(len(vocab), p=probs)])          # Abuja: with this seed, sampling picked the runner-up
```

Two ways to choose:

- **Greedy:** always take the most likely token (`argmax`). Deterministic, sometimes repetitive.
- **Sampling:** pick at random according to the probabilities. More varied. On older models, **temperature** divided the logits by a number before the softmax: below 1 sharpened the distribution, above 1 flattened it. You'll see it in older code and open-source models.

And the loss that trains this? **Cross-entropy**: `−log(probability the model gave to the correct next token)`. If the model gave the right token probability 0.9, the loss is `−log 0.9 ≈ 0.105`; if it gave 0.01, the loss is `≈ 4.6`. Training an LLM is gradient descent on that number, averaged over trillions of tokens.

```python
import numpy as np

probs = np.array([0.675, 0.274, 0.030, 0.002, 0.018])
correct = 0                                   # "Lagos"
print(round(-np.log(probs[correct]), 3))      # 0.393   confident and right: low loss
print(round(-np.log(probs[3]), 3))            # 6.215   if "pizza" had been right: high loss
```

## How this relates to embeddings

An embedding model is a neural network too. Instead of ending in a softmax, it outputs the vector from a late layer (often normalised to length 1). Training pushes texts with similar meaning towards similar directions, which is exactly what makes the cosine similarity from *Vectors, the dot product and cosine similarity* work for search.

## Common mistakes

- **No activation between layers.** `x @ W1 @ W2` collapses into one linear layer. The non-linearity is what gives depth its power.
- **Naive softmax.** `np.exp(z) / np.exp(z).sum()` returns `nan` for large logits. Subtract the max.
- **Softmax along the wrong axis.** For a batch of shape `(n, C)`, each row must sum to 1: use `axis=-1` (or `axis=1`). `axis=0` normalises down each column, mixing different examples.
- **Confusing logits and probabilities.** Logits can be any real number, including negative; they aren't probabilities until softmax. APIs that return "logprobs" return `log(probability)`, which is not the same as logits either.
- **Weight shapes the wrong way round.** With inputs as rows, `W` is `(in, out)` and you write `X @ W`. If the shapes don't fit, check the convention before reaching for `.T`.

## Recap

- A neuron is a dot product plus a bias, then an activation: `a = act(w · x + b)`.
- ReLU for hidden layers; sigmoid for a single probability; softmax to turn a vector of logits into a distribution. Make softmax stable by subtracting the max.
- A layer is `act(X @ W + b)`: one matrix multiply for a whole batch. A network is layers in a row; the forward pass runs them in order.
- An LLM's last layer outputs logits over its vocabulary; softmax gives next-token probabilities; greedy or sampled decoding picks one.
- Classification and language models train on cross-entropy, `−log p(correct)`, by gradient descent.
