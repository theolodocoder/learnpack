# Semantic search over a list of texts

Write a function that finds the texts most similar to a query, using any embedding function you're given:

```python
def semantic_search(query: str, texts: list[str], embed, k: int = 3) -> list[tuple[int, float]]: ...
```

- `embed` takes a **list** of strings and returns a NumPy array with one row per string. In tests it's `fake_embed.embed` (rows already normalised); in a real app it would wrap Voyage AI or sentence-transformers.
- Return up to `k` pairs `(index_into_texts, score)`, best first, where `score` is the **cosine similarity** as a plain Python `float`.
- Don't assume `embed` normalises: normalise the rows yourself (leave all-zero rows as zeros, so their score is `0.0`).
- Ties keep the lower index first (`np.argsort(-scores, kind="stable")`).
- Call `embed` **once** for all the texts (that's batching) and once for the query.
- If `texts` is empty or `k <= 0`, return `[]` without calling `embed`.

## Example

```python
from fake_embed import embed

texts = ["Refunds are issued within 30 days.", "We ship to Lagos and Accra.", "Refund requests need a receipt."]
semantic_search("how do I get a refund", texts, embed, k=2)
# [(2, 0.353...), (0, 0.316...)]
```

The scores come from the toy `fake_embed` model, which matches shared words. A real model would also match "money back" to "refund".
