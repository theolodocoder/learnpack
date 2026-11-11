import numpy as np


def _normalise(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


def semantic_search(query: str, texts: list[str], embed, k: int = 3) -> list[tuple[int, float]]:
    """Top-k (index, cosine similarity) pairs for query against texts, best first."""
    if not texts or k <= 0:
        return []
    docs = _normalise(np.asarray(embed(texts), dtype=float))
    q = _normalise(np.asarray(embed([query]), dtype=float))[0]
    scores = docs @ q
    order = np.argsort(-scores, kind="stable")[:k]
    return [(int(i), float(scores[i])) for i in order]


if __name__ == "__main__":
    from fake_embed import embed

    texts = ["Refunds are issued within 30 days.", "We ship to Lagos and Accra.", "Refund requests need a receipt."]
    for i, score in semantic_search("how do I get a refund", texts, embed, k=2):
        print(f"{score:.3f}  {texts[i]}")
