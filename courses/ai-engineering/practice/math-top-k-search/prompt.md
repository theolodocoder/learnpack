# Semantic search with `top_k`

You have a matrix of document embeddings (one row per document) and the embedding of a query. Return the indices of the `k` documents most similar to the query by **cosine similarity**, most similar first.

```python
def top_k(query, docs, k: int) -> list[int]: ...
```

- `query`: a 1-D array (or list) of length `d`.
- `docs`: a 2-D array (or list of lists) of shape `(n, d)`.
- Return a plain `list` of Python `int`s.
- **Ties:** if two documents have exactly the same score, the lower index comes first. (`np.argsort(-scores, kind="stable")` does this for you.)
- **Edge cases:**
  - if `k` is larger than the number of documents, return all of them, ranked;
  - if `k <= 0`, return `[]`;
  - a document (or query) that is all zeros has similarity `0.0`.

Hint: normalise the rows of `docs` and the query, then `docs_unit @ query_unit` gives every score in one line.

## Example

```python
docs = [[1, 0], [0.9, 0.1], [0, 1], [-1, 0]]
top_k([1, 0], docs, 2)     # [0, 1]
top_k([1, 0], docs, 10)    # [0, 1, 2, 3]
```
