# Project: tiny semantic search and a tiny network, from scratch

Two small systems, built with nothing but NumPy and what you learned in this section. Together they cover both halves of what an AI engineer does with models: **using** them (embeddings and similarity search) and **understanding how they're trained** (forward pass, backpropagation, gradient descent).

You build it in the platform: it's the last exercise in *Backpropagation, and what's next*, called **Project: tiny semantic search and a tiny network**. Check runs the tests offline in under a second.

## Part 1: semantic search

The core of every vector database, in two functions:

- `build_index(doc_vectors)`: normalise every embedding to length 1, once, up front. Handle the zero vector without producing `nan`.
- `search(index, query, k)`: score every document with one matrix–vector multiply, then return the top `k` as `(doc_index, cosine_score)` pairs, best first. Handle `k` larger than the number of documents, `k <= 0`, and a zero query.

Why it matters: when you build RAG in the main track, a database such as pgvector will do this for you at scale. After this, you'll know exactly what it's computing, why it wants normalised vectors, and why "cosine distance" is `1 − cosine similarity`.

## Part 2: a network that learns XOR

XOR (`[0,0]→0`, `[0,1]→1`, `[1,0]→1`, `[1,1]→0`) can't be separated by a single straight line, so a linear model fails. A network with one hidden ReLU layer can learn it.

- `predict(params, X)`: the forward pass, `relu(X @ W1 + b1) @ W2 + b2`.
- `train(X, y, hidden, lr, steps, seed)`: full-batch gradient descent on mean squared error, with your own backward pass. Record the loss at every step.

The tests check that the loss falls below `0.001` and the rounded predictions are exactly XOR.

## Stretch goals (optional, not checked)

- Plot or print the loss every 100 steps and describe the curve: fast fall, plateau, then convergence?
- Try `lr` values of `0.01`, `0.1` and `1.0`. Which is fastest? Which diverges?
- Set `hidden=2` and try several seeds. Some runs get stuck. Why? (Hint: count the dead ReLU units.)
- Replace your hand-made search vectors with real embeddings from an embedding API once you reach the RAG lessons, and run the same `search`.
- Rebuild Part 2 in PyTorch after you start Karpathy's *Zero to Hero*, and confirm `loss.backward()` gives the same gradients as yours.

## Done when

You've passed every exercise in this section, and the project exercise passes all its tests.
