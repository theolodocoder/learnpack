import numpy as np


class EmbeddingCache:
    """Wraps an embed(texts) -> array function with deduplication, batching and caching."""

    def __init__(self, embed, batch_size: int = 128):
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        self._embed = embed
        self.batch_size = batch_size
        self.cache: dict[str, np.ndarray] = {}

    def embed(self, texts: list[str]) -> np.ndarray:
        """One row per text, in order. Only uncached texts are embedded, once each, in batches."""
        if not texts:
            return np.empty((0, 0))
        new = [t for t in dict.fromkeys(texts) if t not in self.cache]
        for start in range(0, len(new), self.batch_size):
            batch = new[start:start + self.batch_size]
            for text, vec in zip(batch, self._embed(batch)):
                self.cache[text] = vec
        return np.array([self.cache[t] for t in texts])


if __name__ == "__main__":
    from fake_embed import embed

    def noisy_embed(texts):
        print("  embedding batch:", texts)
        return embed(texts)

    cache = EmbeddingCache(noisy_embed, batch_size=2)
    print(cache.embed(["a cat", "a dog", "a cat"]).shape)
    print(cache.embed(["a dog", "a fish"]).shape)
