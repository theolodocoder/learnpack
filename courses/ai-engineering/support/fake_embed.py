"""A fake embedding model for offline, free, repeatable exercise tests.

Real embedding models (Voyage AI, sentence-transformers, ...) map text to vectors so that texts
with similar *meaning* end up close together. This toy maps text to vectors so that texts that
share *words* end up close together, which is enough to build and test a RAG pipeline offline:

  1. lowercase the text and split it into words,
  2. drop a few very common words ("the", "is", ...) and crudely strip endings
     ("refunds" -> "refund", "requested" -> "request"),
  3. hash each word to one of DIM slots and count,
  4. L2-normalise each row, so a dot product between two rows is their cosine similarity.

    from fake_embed import embed, DIM

    vecs = embed(["Refunds take 30 days", "How long does a refund take?"])
    vecs.shape            # (2, 256)
    float(vecs[0] @ vecs[1])   # ~0.58: they share "refund" and "take"

It's deterministic (same text, same vector, on every machine) and needs no network or key.
It does NOT understand synonyms: "car" and "automobile" score 0. Real models do.
Text with no usable words (e.g. "" or "the") embeds to an all-zero row.
"""
import re
import zlib

import numpy as np

DIM = 256

STOPWORDS = frozenset(
    "a an and are as at be by can do does for from has have how i in is it its me my of on or "
    "our so that the their there this to was we what when where which who why will with you your".split()
)


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokens(text: str) -> list[str]:
    """The words the fake model 'sees' in a text, after lowercasing, stopwords and stemming."""
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


def embed(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts. Returns a float32 array of shape (len(texts), DIM), rows L2-normalised."""
    if isinstance(texts, str):
        raise TypeError("embed() takes a list of strings; wrap a single text as [text]")
    out = np.zeros((len(texts), DIM), dtype=np.float32)
    for row, text in enumerate(texts):
        for word in tokens(text):
            out[row, zlib.crc32(word.encode()) % DIM] += 1.0
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.where(norms == 0, 1.0, norms)


if __name__ == "__main__":
    v = embed(["Refunds take 30 days", "How long does a refund take?", "The office cat is called Biscuit", ""])
    assert v.shape == (4, DIM) and v.dtype == np.float32
    assert np.allclose(np.linalg.norm(v[:3], axis=1), 1.0), "rows should be unit length"
    assert not v[3].any(), "empty text should embed to zeros"
    assert v[0] @ v[1] > 0.4, "texts sharing words should be similar"
    assert v[0] @ v[2] < 0.1, "unrelated texts should not be"
    assert np.array_equal(embed(["same text"]), embed(["same text"])), "should be deterministic"
    assert embed([]).shape == (0, DIM)
    print("fake_embed ok", round(float(v[0] @ v[1]), 3), round(float(v[0] @ v[2]), 3))
