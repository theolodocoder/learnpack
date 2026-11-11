# An approval gate for risky tools

Put a gate between the model and your tools. Read-only tools run freely; anything with side effects needs a human's yes; every decision is logged.

```python
class ApprovalGate:
    def __init__(self, risks: dict[str, str], approve, *, dry_run: bool = False): ...
    def run(self, name: str, input: dict, handler) -> dict: ...
    log: list[dict]
```

- `risks` maps a tool name to `"read"`, `"write"` or `"irreversible"`. A tool **not** in `risks` is treated as `"irreversible"` (deny by default).
- `approve(name, input) -> bool` asks a human. It's injected so tests (and a CLI, Slack bot or web UI) can supply their own.
- `handler(input) -> str` runs the real tool.

`run` returns a dict shaped like the body of a `tool_result`: `{"content": str, "is_error": bool}`.

| Situation | Ask `approve`? | Run handler? | Returns | `decision` logged |
|---|---|---|---|---|
| risk `"read"` | no | yes | `{"content": result, "is_error": False}` | `"auto"` |
| `dry_run=True` and risk isn't `"read"` | no | **no** | `{"content": "DRY RUN: would call {name} with {input}", "is_error": False}` | `"dry_run"` |
| approve returns `True` | yes | yes | `{"content": result, "is_error": False}` | `"approved"` |
| approve returns `False` **or raises** (e.g. the reviewer timed out) | yes | **no** | `{"content": "Denied by reviewer: ...", "is_error": True}` | `"denied"` |

If the handler itself raises, return `{"content": "<ErrorType>: <message>", "is_error": True}` (the decision stays as it was).

Every call to `run` appends one entry to `self.log`:

```python
{"tool": name, "input": input, "risk": risk, "decision": "approved"}
```

## Example

```python
gate = ApprovalGate({"get_order": "read", "refund": "irreversible"}, approve=lambda n, i: i["amount"] <= 50)
gate.run("get_order", {"id": "A1"}, lambda i: "order A1: shipped")
# {"content": "order A1: shipped", "is_error": False}       (no approval asked)
gate.run("refund", {"amount": 500}, do_refund)
# {"content": "Denied by reviewer: refund was not approved", "is_error": True}   (do_refund never ran)
```
