END = "__end__"


class Graph:
    def __init__(self):
        self.nodes = {}   # name -> fn
        self.edges = {}   # name -> next node name
        self.routers = {} # name -> router fn
        self.entry = None

    def add_node(self, name: str, fn) -> None:
        self.nodes[name] = fn

    def add_edge(self, src: str, dst: str) -> None:
        self.edges[src] = dst

    def add_conditional_edge(self, src: str, router) -> None:
        self.routers[src] = router

    def set_entry(self, name: str) -> None:
        self.entry = name

    def run(self, state: dict, max_steps: int = 25, checkpoints: list | None = None) -> dict:
        """Run from the entry node until END. Returns the final state."""
        # TODO: state = dict(state); current = self.entry
        # TODO: loop at most max_steps times:
        #       state = {**state, **self.nodes[current](state)}
        #       if checkpoints is not None: checkpoints.append((current, dict(state)))
        #       next = edge target, or router(state); neither -> ValueError
        #       next == END -> return state
        # TODO: raise RuntimeError when the step budget runs out
        raise NotImplementedError


if __name__ == "__main__":
    g = Graph()
    g.add_node("draft", lambda s: {"draft": f"v{s['tries'] + 1}", "tries": s["tries"] + 1})
    g.add_node("review", lambda s: {"ok": s["tries"] >= 2})
    g.set_entry("draft")
    g.add_edge("draft", "review")
    g.add_conditional_edge("review", lambda s: END if s["ok"] else "draft")
    saved = []
    try:
        print(g.run({"tries": 0}, checkpoints=saved))
        for step in saved:
            print(step)
    except NotImplementedError:
        print("Write Graph.run first, then Run again.")
