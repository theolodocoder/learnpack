import numpy as np


def semantic_search(query: str, texts: list[str], embed, k: int = 3) -> list[tuple[int, float]]:
    """Top-k (index, cosine similarity) pairs for query against texts, best first."""
    # TODO: return [] early for no texts or k <= 0
    # TODO: doc_vecs = embed(texts); q = embed([query])[0]   (two calls in total)
    # TODO: normalise rows (zeros stay zeros), scores = docs @ q
    # TODO: order = np.argsort(-scores, kind="stable")[:k]
    raise NotImplementedError


if __name__ == "__main__":
    from fake_embed import embed

    texts = ["Refunds are issued within 30 days.", "We ship to Lagos and Accra.", "Refund requests need a receipt."]
    try:
        for i, score in semantic_search("how do I get a refund", texts, embed, k=2):
            print(f"{score:.3f}  {texts[i]}")
    except NotImplementedError:
        print("Write semantic_search, then Run again.")
