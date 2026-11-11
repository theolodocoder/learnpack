# An in-memory vector store

Build the retriever for your RAG pipeline: a class that embeds chunks, keeps their vectors in a NumPy matrix, and returns the most similar chunks for a query.

```python
class VectorStore:
    def __init__(self, embed): ...
    def add(self, chunks: list[dict]) -> None: ...
    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[tuple[dict, float]]: ...
    def __len__(self) -> int: ...
```

- `embed` takes a list of strings and returns an array, one row per string (tests use `fake_embed.embed`).
- **`add(chunks)`**: each chunk is a dict with at least a `"text"` key. Embed all their texts in **one** call, normalise the rows (all-zero rows stay zero), and append them to the matrix (`np.vstack`). Calling `add` several times keeps everything. `add([])` does nothing.
- **`search(query, k, min_score)`**: embed the query, score every chunk by cosine similarity, and return up to `k` `(chunk, score)` pairs, best first, with `score` a Python `float`. The chunk is the same dict you added. Ties keep insertion order. If `min_score` is given, leave out results scoring below it. An empty store or `k <= 0` returns `[]`.
- **`len(store)`** is the number of chunks added.

## Example

```python
from fake_embed import embed

store = VectorStore(embed)
store.add([{"id": "p#0", "text": "Refunds can be requested within 30 days of purchase."},
           {"id": "p#1", "text": "We ship to Lagos, Abuja and Accra."}])
store.search("How many days do I have to request a refund?", k=1)
# [({'id': 'p#0', 'text': 'Refunds can be requested within 30 days of purchase.'}, 0.612...)]
store.search("What is the capital of Peru?", min_score=0.3)
# []
```
