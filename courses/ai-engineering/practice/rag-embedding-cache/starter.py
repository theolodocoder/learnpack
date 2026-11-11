import numpy as np


class EmbeddingCache:
    """Wraps an embed(texts) -> array function with deduplication, batching and caching."""

    def __init__(self, embed, batch_size: int = 128):
        # TODO: validate batch_size, keep embed, create the cache dict
        self._embed = embed
        self.batch_size = batch_size
        self.cache: dict[str, np.ndarray] = {}

    def embed(self, texts: list[str]) -> np.ndarray:
        """One row per text, in order. Only uncached texts are embedded, once each, in batches."""
        # TODO: new = texts not in the cache, deduplicated in first-seen order (dict.fromkeys helps)
        # TODO: for each batch of new texts: vecs = self._embed(batch); store each row in self.cache
        # TODO: return np.array([self.cache[t] for t in texts])
        raise NotImplementedError


if __name__ == "__main__":
    from fake_embed import embed

    def noisy_embed(texts):
        print("  embedding batch:", texts)
        return embed(texts)

    cache = EmbeddingCache(noisy_embed, batch_size=2)
    try:
        print(cache.embed(["a cat", "a dog", "a cat"]).shape)
        print(cache.embed(["a dog", "a fish"]).shape)
    except NotImplementedError:
        print("Write EmbeddingCache.embed, then Run again.")
