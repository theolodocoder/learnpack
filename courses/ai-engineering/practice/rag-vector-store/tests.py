import math

from fake_embed import embed
from solution import VectorStore

CHUNKS = [
    {"id": "policy.md#0", "text": "Refunds can be requested within 30 days of purchase."},
    {"id": "policy.md#1", "text": "Gift purchases are refunded as store credit."},
    {"id": "shipping.md#0", "text": "We ship to Lagos, Abuja and Accra."},
    {"id": "office.md#0", "text": "The office cat is called Biscuit."},
]


def make():
    store = VectorStore(embed)
    store.add(CHUNKS[:2])
    store.add(CHUNKS[2:])
    return store


def test_add_keeps_all_chunks():
    store = make()
    assert len(store) == 4, f"two add() calls with 2 chunks each should give len 4, got {len(store)}"
    store.add([])
    assert len(store) == 4, "add([]) should change nothing"


def test_search_ranks_by_similarity():
    hits = make().search("How many days do I have to request a refund?", k=2)
    ids = [c["id"] for c, _ in hits]
    assert ids[0] == "policy.md#0", f"the 30-day refund chunk should rank first, got {ids!r}"
    assert len(hits) == 2, f"k=2 should give 2 results, got {len(hits)}"
    assert hits[0][1] >= hits[1][1], "results must be sorted best first"
    assert hits[0][0] is CHUNKS[0], "return the same chunk dicts you were given"


def test_scores_are_cosine_floats():
    hits = make().search("ship to Accra", k=1)
    chunk, score = hits[0]
    want = float(embed(["ship to Accra"])[0] @ embed([chunk["text"]])[0])
    assert type(score) is float, f"scores should be Python floats, got {type(score).__name__}"
    assert math.isclose(score, want, rel_tol=1e-5), f"expected cosine similarity {want:.4f}, got {score:.4f}"


def test_min_score_filters_irrelevant_chunks():
    store = make()
    assert store.search("What is the capital of Peru?", k=3, min_score=0.3) == [], \
        "nothing should pass min_score=0.3 for an off-topic question"
    hits = store.search("refund", k=4, min_score=0.2)
    assert {c["id"] for c, _ in hits} == {"policy.md#0", "policy.md#1"}, f"only the refund chunks should pass, got {hits!r}"
    assert all(s >= 0.2 for _, s in hits), "every returned score must be >= min_score"


def test_empty_store_and_k_zero():
    calls = []

    def counting(texts):
        calls.append(texts)
        return embed(texts)

    empty = VectorStore(counting)
    assert empty.search("anything") == [], "an empty store should return []"
    assert make().search("refund", k=0) == [], "k=0 should return []"


def test_add_embeds_in_one_batch():
    calls = []

    def counting(texts):
        calls.append(list(texts))
        return embed(texts)

    store = VectorStore(counting)
    store.add(CHUNKS)
    assert calls == [[c["text"] for c in CHUNKS]], f"add() should embed all texts in one call, got {len(calls)} calls"
