import numpy as np

from fake_embed import embed
from solution import EmbeddingCache


def recorder():
    calls = []

    def fn(texts):
        calls.append(list(texts))
        return embed(texts)

    return fn, calls


def test_returns_rows_in_order_with_repeats():
    fn, _ = recorder()
    texts = ["a cat", "a dog", "a cat"]
    got = EmbeddingCache(fn).embed(texts)
    assert got.shape[0] == 3, f"expected 3 rows (one per input), got shape {got.shape}"
    assert np.allclose(got, embed(texts)), "row i must be the embedding of texts[i]"


def test_each_text_embedded_once():
    fn, calls = recorder()
    cache = EmbeddingCache(fn)
    cache.embed(["a cat", "a dog", "a cat"])
    assert calls == [["a cat", "a dog"]], f"expected one call with the unique texts in order, got {calls!r}"


def test_cached_texts_are_not_embedded_again():
    fn, calls = recorder()
    cache = EmbeddingCache(fn)
    cache.embed(["a cat", "a dog"])
    got = cache.embed(["a dog", "a fish", "a cat"])
    assert calls == [["a cat", "a dog"], ["a fish"]], f"only 'a fish' is new the second time; calls were {calls!r}"
    assert np.allclose(got, embed(["a dog", "a fish", "a cat"])), "rows must still match the input order"


def test_batches_respect_batch_size():
    fn, calls = recorder()
    texts = [f"text number {i}" for i in range(7)]
    EmbeddingCache(fn, batch_size=3).embed(texts)
    sizes = [len(c) for c in calls]
    assert sizes == [3, 3, 1], f"7 new texts with batch_size=3 should be batches of [3, 3, 1], got {sizes!r}"
    assert [t for c in calls for t in c] == texts, "batches should cover the texts in order"


def test_empty_input_and_bad_batch_size():
    fn, calls = recorder()
    got = EmbeddingCache(fn).embed([])
    assert len(got) == 0 and calls == [], "an empty list should return length 0 without calling embed"
    try:
        EmbeddingCache(fn, batch_size=0)
    except ValueError:
        return
    raise AssertionError("batch_size=0 should raise ValueError")
