import numpy as np


def normalise(m: np.ndarray) -> np.ndarray:
    """Divide each row by its length; all-zero rows stay zero."""
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


class VectorStore:
    def __init__(self, embed):
        self.embed = embed
        self.chunks: list[dict] = []
        self.vectors: np.ndarray | None = None

    def add(self, chunks: list[dict]) -> None:
        """Embed the chunks' texts in one call and append the normalised rows."""
        if not chunks:
            return
        vecs = normalise(np.asarray(self.embed([c["text"] for c in chunks]), dtype=float))
        self.vectors = vecs if self.vectors is None else np.vstack([self.vectors, vecs])
        self.chunks.extend(chunks)

    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[tuple[dict, float]]:
        """Up to k (chunk, cosine score) pairs, best first, skipping scores below min_score."""
        if self.vectors is None or k <= 0:
            return []
        q = normalise(np.asarray(self.embed([query]), dtype=float))[0]
        scores = self.vectors @ q
        hits = []
        for i in np.argsort(-scores, kind="stable")[:k]:
            if min_score is not None and scores[i] < min_score:
                break
            hits.append((self.chunks[i], float(scores[i])))
        return hits

    def __len__(self) -> int:
        return len(self.chunks)


if __name__ == "__main__":
    from fake_embed import embed

    store = VectorStore(embed)
    store.add([{"id": "p#0", "text": "Refunds can be requested within 30 days of purchase."},
               {"id": "p#1", "text": "We ship to Lagos, Abuja and Accra."}])
    print(store.search("How many days do I have to request a refund?", k=1))
    print(store.search("What is the capital of Peru?", min_score=0.3))
