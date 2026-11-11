import math

import numpy as np

from fake_embed import embed
from solution import semantic_search

TEXTS = [
    "Refunds are issued within 30 days.",
    "We ship to Lagos and Accra.",
    "Refund requests need a receipt.",
    "The office cat is called Biscuit.",
]


def test_finds_most_similar_first():
    got = semantic_search("how do I get a refund", TEXTS, embed, k=2)
    idx = [i for i, _ in got]
    assert idx == [2, 0], f"expected the two refund texts [2, 0] (text 2 shares more of its words), got {idx!r}"
    assert all(type(s) is float for _, s in got), "scores should be plain Python floats"
    assert got[0][1] >= got[1][1], "results must be sorted best first"


def test_scores_are_cosine_similarity():
    got = dict(semantic_search("refund receipt", TEXTS, embed, k=4))
    q = embed(["refund receipt"])[0]
    want = float(embed([TEXTS[2]])[0] @ q)
    assert math.isclose(got[2], want, rel_tol=1e-5), f"score for text 2 should be {want:.4f}, got {got[2]:.4f}"


def test_normalises_unnormalised_embeddings():
    def raw_embed(texts):
        return embed(texts) * 7.0  # same directions, length 7

    got = semantic_search("how do I get a refund", TEXTS, raw_embed, k=1)
    assert got[0][0] == 2 and got[0][1] <= 1.0 + 1e-6, f"normalise rows so scores stay cosine similarities, got {got!r}"


def test_batches_texts_in_one_call():
    calls = []

    def counting_embed(texts):
        calls.append(list(texts))
        return embed(texts)

    semantic_search("refund", TEXTS, counting_embed, k=2)
    assert len(calls) == 2, f"embed should be called twice (all texts, then the query), got {len(calls)} calls"
    assert TEXTS in calls, "embed all the texts in a single call"


def test_k_bigger_than_texts_and_empty_inputs():
    got = semantic_search("refund", TEXTS, embed, k=10)
    assert sorted(i for i, _ in got) == [0, 1, 2, 3], f"k larger than len(texts) should return all of them, got {got!r}"

    def boom(texts):
        raise AssertionError("embed should not be called")

    assert semantic_search("refund", [], boom) == [], "no texts should give []"
    assert semantic_search("refund", TEXTS, boom, k=0) == [], "k=0 should give []"


def test_zero_vector_scores_zero():
    def embed_with_blank(texts):
        return np.vstack([np.zeros(4), np.array([1.0, 0, 0, 0])]) if len(texts) == 2 else np.array([[1.0, 0, 0, 0]])

    got = semantic_search("q", ["the", "x"], embed_with_blank, k=2)
    assert got == [(1, 1.0), (0, 0.0)], f"an all-zero row should score 0.0 (not nan), got {got!r}"
