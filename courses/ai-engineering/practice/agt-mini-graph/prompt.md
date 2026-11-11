# A tiny state graph, framework-style

Frameworks like LangGraph model an agent as a **graph**: nodes are functions that read the shared state and return updates, edges say what runs next, and a checkpoint is saved after every step so a run can be inspected or resumed. Build the core of that in plain Python to see there's no magic.

```python
END = "__end__"

class Graph:
    def add_node(self, name: str, fn) -> None: ...          # fn(state: dict) -> dict of updates
    def add_edge(self, src: str, dst: str) -> None: ...     # always go src -> dst
    def add_conditional_edge(self, src: str, router) -> None: ...  # router(state) -> next node name or END
    def set_entry(self, name: str) -> None: ...
    def run(self, state: dict, max_steps: int = 25, checkpoints: list | None = None) -> dict: ...
```

`run`:

1. Start at the entry node with a **copy** of `state` (never modify the caller's dict).
2. Run the node: `updates = fn(state)`, then `state = {**state, **updates}`.
3. If `checkpoints` is a list, append `(node_name, dict(state))` after each step.
4. Pick the next node: the plain edge's target, or `router(state)` for a conditional edge. A node with neither raises `ValueError`.
5. Stop and return the state when the next node is `END`. If you've run `max_steps` nodes and haven't reached `END`, raise `RuntimeError` (a graph with a cycle must still have a budget).

## Example

```python
g = Graph()
g.add_node("draft", lambda s: {"draft": f"v{s['tries'] + 1}", "tries": s["tries"] + 1})
g.add_node("review", lambda s: {"ok": s["tries"] >= 2})
g.set_entry("draft")
g.add_edge("draft", "review")
g.add_conditional_edge("review", lambda s: END if s["ok"] else "draft")

g.run({"tries": 0})
# {"tries": 2, "draft": "v2", "ok": True}     (draft -> review -> draft -> review -> END)
```
