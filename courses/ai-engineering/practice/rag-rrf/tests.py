import math

from solution import reciprocal_rank_fusion


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9)


def test_fuses_two_lists():
    got = reciprocal_rank_fusion([["A", "B", "C"], ["C", "A", "D"]])
    ids = [d for d, _ in got]
    assert ids == ["A", "C", "B", "D"], f"expected order ['A', 'C', 'B', 'D'], got {ids!r}"
    want = {"A": 1/61 + 1/62, "C": 1/63 + 1/61, "B": 1/62, "D": 1/63}
    for d, s in got:
        assert close(s, want[d]), f"score for {d} should be {want[d]:.6f}, got {s:.6f}"


def test_single_list_keeps_its_order():
    got = reciprocal_rank_fusion([["x", "y", "z"]], k=1)
    assert [d for d, _ in got] == ["x", "y", "z"], f"one list should keep its order, got {got!r}"
    assert close(got[0][1], 1 / 2) and close(got[2][1], 1 / 4), f"with k=1, ranks 1 and 3 score 1/2 and 1/4, got {got!r}"


def test_agreement_beats_one_top_rank():
    # "both" is 2nd in both lists; "solo" is 1st in only one.
    got = reciprocal_rank_fusion([["solo", "both"], ["other", "both"]])
    assert got[0][0] == "both", f"an id ranked well by both lists should win, got {got!r}"


def test_ties_broken_by_id():
    got = reciprocal_rank_fusion([["b", "x"], ["a", "y"]])
    assert [d for d, _ in got] == ["a", "b", "x", "y"], f"equal scores should be ordered by id, got {got!r}"


def test_duplicates_count_once_per_list():
    got = dict(reciprocal_rank_fusion([["A", "A", "B"]]))
    assert close(got["A"], 1 / 61), f"A should only count at its first position (1/61), got {got['A']}"
    assert close(got["B"], 1 / 63), f"B is at rank 3 even though A repeated, so 1/63; got {got['B']}"


def test_empty_inputs():
    assert reciprocal_rank_fusion([]) == [], "no lists gives []"
    assert reciprocal_rank_fusion([[], []]) == [], "empty lists give []"
