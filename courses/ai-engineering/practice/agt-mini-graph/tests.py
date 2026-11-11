from solution import END, Graph


def review_loop():
    g = Graph()
    g.add_node("draft", lambda s: {"draft": f"v{s['tries'] + 1}", "tries": s["tries"] + 1})
    g.add_node("review", lambda s: {"ok": s["tries"] >= 2})
    g.set_entry("draft")
    g.add_edge("draft", "review")
    g.add_conditional_edge("review", lambda s: END if s["ok"] else "draft")
    return g


def test_linear_graph_merges_updates():
    g = Graph()
    g.add_node("a", lambda s: {"x": 1})
    g.add_node("b", lambda s: {"y": s["x"] + 1})
    g.set_entry("a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    got = g.run({"start": True})
    assert got == {"start": True, "x": 1, "y": 2}, f"expected merged state, got {got!r}"


def test_conditional_edge_loops_until_done():
    got = review_loop().run({"tries": 0})
    want = {"tries": 2, "draft": "v2", "ok": True}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_checkpoints_record_every_step():
    saved = []
    review_loop().run({"tries": 0}, checkpoints=saved)
    names = [name for name, _ in saved]
    assert names == ["draft", "review", "draft", "review"], f"expected one checkpoint per step, got {names!r}"
    assert saved[0][1] == {"tries": 1, "draft": "v1"}, f"a checkpoint holds the state after that step, got {saved[0][1]!r}"


def test_input_state_is_not_modified():
    start = {"tries": 0}
    review_loop().run(start)
    assert start == {"tries": 0}, f"run must not modify the caller's dict, got {start!r}"


def test_step_budget_and_missing_edge():
    g = Graph()
    g.add_node("spin", lambda s: {"n": s.get("n", 0) + 1})
    g.set_entry("spin")
    g.add_edge("spin", "spin")
    try:
        g.run({}, max_steps=5)
        raise AssertionError("expected RuntimeError for a graph that never reaches END")
    except RuntimeError:
        pass
    dead = Graph()
    dead.add_node("only", lambda s: {})
    dead.set_entry("only")
    try:
        dead.run({})
    except ValueError:
        return
    raise AssertionError("expected ValueError for a node with no outgoing edge")
