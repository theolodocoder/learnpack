import math

from solution import evaluate, recall_at_k, reciprocal_rank


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def test_recall_at_k():
    cases = [
        ((["a", "x", "b"], ["a", "b", "c"], 2), 1 / 3),
        ((["a", "x", "b"], ["a", "b", "c"], 3), 2 / 3),
        ((["x", "y"], ["a"], 2), 0.0),
        ((["a", "b"], ["a", "a", "b"], 5), 1.0),
        ((["a"], [], 3), 0.0),
    ]
    for args, want in cases:
        got = recall_at_k(*args)
        assert close(got, want), f"recall_at_k{args!r} should be {want:.4f}, got {got!r}"


def test_reciprocal_rank():
    cases = [((["a", "b"], ["a"]), 1.0), ((["x", "y", "a"], ["a"]), 1 / 3),
             ((["x", "b", "a"], ["a", "b"]), 0.5), ((["x", "y"], ["a"]), 0.0), (([], ["a"]), 0.0)]
    for args, want in cases:
        got = reciprocal_rank(*args)
        assert close(got, want), f"reciprocal_rank{args!r} should be {want:.4f}, got {got!r}"


def test_evaluate_example():
    golden = [{"question": "q1", "relevant": ["a"]}, {"question": "q2", "relevant": ["b"]}]
    results = {"q1": ["a", "x"], "q2": ["x", "b"]}
    got = evaluate(golden, lambda q: results[q], k=1)
    assert set(got) == {"recall@k", "mrr", "n"}, f"expected keys recall@k, mrr, n; got {sorted(got)!r}"
    assert close(got["recall@k"], 0.5) and close(got["mrr"], 0.75) and got["n"] == 2, \
        f"expected recall@k 0.5, mrr 0.75, n 2; got {got!r}"


def test_evaluate_calls_search_once_per_question():
    calls = []

    def search(q):
        calls.append(q)
        return ["d1", "d2", "d3"]

    golden = [{"question": f"q{i}", "relevant": ["d3"]} for i in range(4)]
    got = evaluate(golden, search, k=2)
    assert calls == ["q0", "q1", "q2", "q3"], f"call search once per question, in order; got {calls!r}"
    assert close(got["recall@k"], 0.0) and close(got["mrr"], 1 / 3), f"d3 is rank 3: recall@2 0, mrr 1/3; got {got!r}"


def test_empty_golden_raises():
    try:
        evaluate([], lambda q: [])
    except ValueError:
        return
    raise AssertionError("an empty golden set should raise ValueError")
