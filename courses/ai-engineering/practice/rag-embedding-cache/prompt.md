# Batch and cache embeddings

Embedding the same text twice wastes money, and one request per text wastes time. Write a small cache that fixes both:

```python
class EmbeddingCache:
    def __init__(self, embed, batch_size: int = 128): ...
    def embed(self, texts: list[str]) -> np.ndarray: ...
```

- `embed` (the constructor argument) takes a list of strings and returns an array with one row per string. In tests it's `fake_embed.embed` wrapped to record its calls.
- `EmbeddingCache.embed(texts)` returns an array with **one row per input text, in the same order**, including repeats.
- Only texts **not already cached** are sent to the underlying `embed`, **each one once** (deduplicate, keeping first-seen order), in batches of at most `batch_size` texts.
- After embedding, store each new vector in the cache (a dict from text to vector is fine).
- An empty list returns an array of length 0 and doesn't call the underlying `embed`.
- `batch_size < 1` raises `ValueError`.

## Example

```python
cache = EmbeddingCache(embed, batch_size=2)
cache.embed(["a cat", "a dog", "a cat"])   # embeds ["a cat", "a dog"] in one batch; returns 3 rows
cache.embed(["a dog", "a fish"])           # embeds only ["a fish"]
```

In real code you'd also put the model name in the cache key, so switching models can't return stale vectors.
