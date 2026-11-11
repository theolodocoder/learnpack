# Humans in the loop

## Why this matters

The first time a client lets your agent touch real systems, they'll ask one question: "what stops it doing something stupid?" A good answer is not "the prompt tells it to be careful". It's this: read-only tools run freely, anything that changes the world needs a person's approval, every action is logged, there's a dry-run mode for testing, and hard limits on time and money stop runaway runs. This lesson builds those controls, and shows how to design tools so the mistakes that slip through are cheap.

## 1. Risk levels for tools

Sort every tool into one of three levels before you write a line of the agent:

| Level | Examples | Default policy |
|---|---|---|
| **Read-only** | `get_order`, `search_docs`, `list_invoices`, `fetch_url` (allowlisted) | Run automatically |
| **Side-effecting, reversible** | `draft_reply`, `add_note`, `create_ticket`, `update_address` | Needs approval, or auto-run with an easy undo |
| **Irreversible or costly** | `send_email`, `refund_payment`, `delete_record`, `post_publicly`, `place_order` | Always needs approval |

Make the levels data, not scattered `if` statements:

```python
RISKS = {
    "get_order": "read",
    "search_orders": "read",
    "draft_reply": "write",
    "send_reply": "irreversible",
    "refund": "irreversible",
}
```

And **deny by default**: a tool missing from the table is treated as irreversible. Someone will add a tool later and forget to classify it; that mistake should make the agent more careful, not less.

> **Note:** "Read-only" is about effects, not the HTTP verb. A `fetch_url` tool that can reach `https://api.example.com/delete?id=7` is not read-only, and a read tool can still leak data if its output goes somewhere public. Classify by what can go wrong.

## 2. An approval gate

Put one function between the agent loop and every tool. It checks the risk, asks a human when needed, and records the decision:

```python
class ApprovalGate:
    def __init__(self, risks: dict[str, str], approve, *, dry_run: bool = False):
        self.risks, self.approve, self.dry_run = risks, approve, dry_run
        self.log: list[dict] = []

    def run(self, name: str, input: dict, handler) -> dict:
        risk = self.risks.get(name, "irreversible")
        if risk == "read":
            decision = "auto"
        elif self.dry_run:
            decision = "dry_run"
        else:
            try:
                decision = "approved" if self.approve(name, input) else "denied"
            except Exception:                     # reviewer timed out or the UI crashed
                decision = "denied"
        self.log.append({"tool": name, "input": input, "risk": risk, "decision": decision})

        if decision == "dry_run":
            return {"content": f"DRY RUN: would call {name} with {input}", "is_error": False}
        if decision == "denied":
            return {"content": f"Denied by reviewer: {name} was not approved", "is_error": True}
        try:
            return {"content": str(handler(input)), "is_error": False}
        except Exception as e:
            return {"content": f"{type(e).__name__}: {e}", "is_error": True}
```

Plug it into the loop where you used to call the handler directly:

```python
for block in response.content:
    if block.type == "tool_use":
        outcome = gate.run(block.name, block.input, HANDLERS.get(block.name, unknown_tool))
        results.append({"type": "tool_result", "tool_use_id": block.id, **outcome})
```

Three properties make this robust:

- **`approve` is injected.** In a terminal it's `input()`; in a web app it's a button; in tests it's a lambda. The gate doesn't care.
- **A failed approval is a denial.** An exception, a timeout, an unclear answer: anything that isn't a clear yes means no.
- **A denial goes back to the model as `is_error`.** The model learns the action didn't happen and can tell the user, propose something else, or ask. It must never believe it sent an email that it didn't.

A simple terminal reviewer:

```python
import json

def ask_in_terminal(name: str, input: dict) -> bool:
    print(f"\nThe agent wants to call {name}:")
    print(json.dumps(input, indent=2))
    return input("Approve? [y/N] ").strip().lower() == "y"     # anything but "y" is a no
```

Show the reviewer **exactly** what will happen: the recipient, the full email body, the amount. "Approve send_email?" without the arguments is a rubber stamp.

### Approval that takes hours

In a web app, nobody is sitting at a terminal. The pattern is to **pause**:

1. The agent requests `refund(order="A1", amount=40)`.
2. Your code saves the agent's state (messages plus the pending tool call) with `status = "waiting_for_approval"` and notifies a human (a dashboard row, a Slack message).
3. The request ends. Nothing is running.
4. When the human clicks Approve or Deny, a handler loads the state, runs (or refuses) the tool, appends the `tool_result`, and continues the loop.

This is why *Memory and state* made state an explicit, saveable object. Frameworks call this an "interrupt"; it's the same idea.

## 3. Dry-run mode

Before you let an agent loose on real data, run it with **dry run** on: read tools work for real, and every side-effecting tool returns a description of what it would have done.

```python
gate = ApprovalGate(RISKS, approve=ask_in_terminal, dry_run=True)
# agent calls refund(order="A1", amount=40)
# -> tool_result: "DRY RUN: would call refund with {'order': 'A1', 'amount': 40}"
```

Dry run is how you test an agent against production data safely, demo it to a client, and run evals that check "would it have refunded the right order?" without refunding anything. Return a success (not an error) so the agent continues its plan and you see the whole sequence.

## 4. Audit logs

The gate's `log` is the start of an **audit trail**: a permanent record of what the agent did, who approved it, and when. For anything a client will rely on, write it somewhere durable:

```python
import json
import sqlite3
from datetime import datetime, timezone

db = sqlite3.connect("audit.db")
db.execute("""CREATE TABLE IF NOT EXISTS audit(
    id INTEGER PRIMARY KEY, at TEXT, run_id TEXT, tool TEXT, input TEXT,
    risk TEXT, decision TEXT, approver TEXT, result TEXT)""")


def audit(run_id, tool, input, risk, decision, approver, result):
    db.execute("INSERT INTO audit(at, run_id, tool, input, risk, decision, approver, result) "
               "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
               (datetime.now(timezone.utc).isoformat(), run_id, tool, json.dumps(input),
                risk, decision, approver, result[:500]))
    db.commit()
```

Rules for audit logs: append only (never update or delete rows from code), include **who** approved, keep timestamps in UTC, and store enough to answer "why did customer X get a refund?" six months later.

## 5. Timeouts and spending limits

Approvals stop bad actions. Limits stop bad **runs**: loops, slow tools, and quiet cost blow-ups.

```python
import time

PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}


class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, max_usd: float, max_seconds: float, max_tool_calls: int):
        self.max_usd, self.max_tool_calls = max_usd, max_tool_calls
        self.deadline = time.monotonic() + max_seconds
        self.spent_usd = 0.0
        self.tool_calls = 0

    def charge(self, model: str, usage) -> None:
        price_in, price_out = PRICES[model]
        self.spent_usd += (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000
        self.check()

    def count_tool_call(self) -> None:
        self.tool_calls += 1
        self.check()

    def check(self) -> None:
        if self.spent_usd > self.max_usd:
            raise BudgetExceeded(f"spent ${self.spent_usd:.2f} of ${self.max_usd:.2f}")
        if self.tool_calls > self.max_tool_calls:
            raise BudgetExceeded(f"{self.tool_calls} tool calls, limit {self.max_tool_calls}")
        if time.monotonic() > self.deadline:
            raise BudgetExceeded("time limit reached")
```

Call `budget.charge(model, response.usage)` after every API call and `budget.count_tool_call()` before every tool. Catch `BudgetExceeded` at the top of the run, save the state, and report it. Also put **per-tool timeouts** on anything that talks to the network (`httpx.Client(timeout=10)`, as in *HTTP and JSON with httpx*); a hung tool otherwise hangs the whole agent.

Business limits belong in code too, not just the prompt: "refunds over $100 always need a manager", "at most 20 emails per run", "never contact a customer twice in a day". The model can be talked out of a rule in its prompt; it can't talk its way past an `if` statement.

## 6. Design tools so mistakes are cheap

The best safety control is a tool that can't do much damage. When you design a tool, shrink what a wrong call can do:

- **Draft, don't send.** `draft_reply` saves a draft for a human to send. Same usefulness, near-zero risk.
- **Narrow tools beat general ones.** `refund_order(order_id, amount)` capped at the order's total beats `create_payment(to_account, amount)`. Never give an agent `run_sql(query)` when `get_order(order_id)` will do.
- **Scope to the current user.** The handler gets the customer id from your session, not from the model. The model can ask for order `A1`; your code only looks in this customer's orders.
- **Soft-delete.** `archive_ticket` instead of `delete_ticket`, with an undo.
- **Bounded inputs.** Pydantic fields with `le=`/`max_length=`, enums instead of free text.
- **Idempotency keys** for payments and sends, so a retried call can't charge twice.
- **Return what happened.** A tool's result should say exactly what changed ("Refunded $40.00 to order A1. New status: refunded."), so the model, the user and the audit log all agree.

> **Try it:** In the practice editor, build `ApprovalGate` and check the dry-run test: the refund handler must never run, but the read tool still does.

## Common mistakes

- **Safety rules only in the prompt.** Prompts guide; code enforces.
- **Allow by default**, so a new unclassified tool runs without approval.
- **Approval prompts without the arguments**, so reviewers approve blindly.
- **Treating a timeout or error from the approval step as a yes.**
- **Telling the model an action succeeded when it was denied**, or not telling it anything.
- **No cost or time limits**, discovered when the invoice arrives.
- **Broad, powerful tools** (`run_sql`, `send_any_email`, `http_request`) where narrow ones would do.
- **Audit logs that code can edit or delete.**

## Recap

- Classify every tool as read-only, reversible or irreversible; unknown tools count as irreversible.
- Route every tool call through an approval gate with an injected `approve` function; anything but a clear yes is a no, and denials go back to the model as `is_error`.
- For slow approvals, save state, stop, and resume when the human answers.
- Dry-run mode runs reads for real and describes writes instead of doing them.
- Keep an append-only audit log; enforce money, time and tool-call limits in code.
- Design narrow, scoped, reversible tools so the mistakes that get through cost little.
