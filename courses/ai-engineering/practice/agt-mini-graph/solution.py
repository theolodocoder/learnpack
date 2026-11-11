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
        state = dict(state)
        current = self.entry
        for _ in range(max_steps):
            state = {**state, **self.nodes[current](state)}
            if checkpoints is not None:
                checkpoints.append((current, dict(state)))
            if current in self.routers:
                current = self.routers[current](state)
            elif current in self.edges:
                current = self.edges[current]
            else:
                raise ValueError(f"node {current!r} has no outgoing edge")
            if current == END:
                return state
        raise RuntimeError(f"graph did not reach END within {max_steps} steps")
