# Evals: measuring LLM features and agents

## Why this matters

You change one sentence in a prompt to fix a complaint, and three other cases quietly break. You upgrade the model and the JSON output gains a trailing comment. Without evals, you find out from users. With evals, you find out in 30 seconds, before you ship. Evals are also what separates "I built an AI demo" from "I built an AI product": being able to say "the agent resolves 87% of our golden tickets correctly, up from 71%" is how you justify every change, win the gig, and keep it.

## 1. What an eval is

An eval is a test suite for a non-deterministic system:

1. **A dataset** of cases: inputs, plus what a good output looks like.
2. **A task** that runs your feature (prompt, RAG pipeline, agent) on each input.
3. **Graders** that score each output.
4. **A report**: pass rate overall and per category, plus the failures to read.

It differs from unit tests in two ways. Outputs vary, so you grade properties ("mentions the refund window", "valid JSON with these keys") rather than exact strings. And you don't expect 100%: you track a **score** and make sure changes move it up.

You did a small version in *Prompt engineering for developers* (classify, then measure) and in *Better retrieval* (recall@k on a golden set). This lesson generalises it to any LLM feature and to agents.

## 2. Golden datasets

A **golden dataset** is a set of cases you trust, kept in version control next to the code:

```json
[
  {"id": "refund-window", "input": "How long do I have to return shoes?",
   "check": "contains", "expected": ["30 days"], "tags": ["policy"]},
  {"id": "order-lookup", "input": "Where is order A1042?",
   "check": "tool_called", "expected": {"name": "get_order", "input": {"order_id": "A1042"}}, "tags": ["tools"]},
  {"id": "extract-json", "input": "Invoice from Ada Ltd, total ₦45,000",
   "check": "json_keys", "expected": ["vendor", "total"], "tags": ["extraction"]}
]
```

Where cases come from, in order of value:

- **Real inputs**: actual user questions, tickets, documents (anonymised). Nothing else captures how people really write.
- **Failures**: every bug report becomes a case. This is how the set grows teeth.
- **Edge cases** you can think of: empty input, other languages, very long input, ambiguous requests, requests the agent should refuse.
- **Adversarial cases**: prompt injection attempts (next lesson), attempts to get out-of-scope actions.

Start with 20–50 cases. That's enough to catch regressions, and small enough to run on every change. Tag cases by category so the report can say "policy questions 95%, tool use 60%" instead of one blurred number.

## 3. Code-graded checks

Use code to grade whenever you can: it's free, fast, deterministic and never has an off day.

```python
import json


def check(case: dict, output) -> bool:
    kind, expected = case["check"], case["expected"]
    if kind == "exact":
        return output.strip() == expected
    if kind == "contains":
        return all(s.lower() in output.lower() for s in expected)
    if kind == "json_keys":
        try:
            data = json.loads(output)
        except ValueError:
            return False
        return isinstance(data, dict) and all(k in data for k in expected)
    if kind == "tool_called":
        return any(c["name"] == expected["name"]
                   and all(c["input"].get(k) == v for k, v in expected["input"].items())
                   for c in output)
    raise ValueError(f"unknown check {kind!r}")
```

What each is good for:

- **Exact match:** classification labels, extracted ids, yes/no answers.
- **Contains / regex:** key facts in a free-text answer ("30 days", an order number). Also **not contains**: the answer must not mention a competitor, a price, or the system prompt.
- **JSON schema:** structured output. Better than checking keys: validate with your Pydantic model, `Invoice.model_validate_json(output)`, so types and constraints are checked too.
- **Tool-call assertions:** for agents, check the agent called the right tool with the right arguments, and did **not** call tools it shouldn't (`refund` on a question that only asked for status).

A runner ties it together:

```python
def run_evals(fn, cases):
    failures = []
    for case in cases:
        try:
            ok = check(case, fn(case["input"]))
        except Exception:
            ok = False                       # crashing is failing
        if not ok:
            failures.append(case["id"])
    passed = len(cases) - len(failures)
    return {"total": len(cases), "passed": passed,
            "pass_rate": passed / len(cases) if cases else 0.0, "failures": failures}
```

Always **read the failures**, not just the number. Half the time the "failure" is a bad test case; the other half it's the insight you needed.

## 4. LLM-as-judge

Some qualities need judgement: is the reply polite? Does it actually answer the question? Is the summary faithful to the source? For these, use a second model call as a **judge**, with a precise **rubric** and **structured output** so the verdict is machine-readable:

```python
from pydantic import BaseModel, Field


class Verdict(BaseModel):
    reasoning: str                  # first, so the judge thinks before it scores
    score: int = Field(ge=1, le=5)
    passed: bool


RUBRIC = """Pass only if ALL are true:
1. The reply answers the customer's actual question.
2. Every fact in the reply appears in the provided policy text.
3. The tone is polite and the reply is under 120 words.
Score 1-5 for overall quality."""


def llm_judge(client, question, answer, rubric, model="claude-opus-5-5") -> Verdict:
    response = client.messages.parse(
        model=model, max_tokens=2000,
        system="You are a strict evaluator. Grade ONLY against the rubric. Reason first, then score.",
        messages=[{"role": "user", "content":
            f"<question>\n{question}\n</question>\n<answer>\n{answer}\n</answer>\n<rubric>\n{rubric}\n</rubric>"}],
        output_format=Verdict,
    )
    return response.parsed_output
```

Making judges trustworthy:

- **Specific rubrics.** "Is it good?" gives noise. A checklist of observable criteria gives consistent verdicts.
- **Reasoning before the score.** Put `reasoning` first in the model so the score follows from it.
- **Give the judge the reference.** For faithfulness, include the source document or the expected answer in tags.
- **Calibrate against humans.** Grade 20–30 outputs yourself, run the judge on the same ones, and check how often you agree. If it's below about 80%, fix the rubric before trusting the judge.
- **Use a strong model for judging**, and don't let the same prompt grade itself without checking it against human labels.
- **Prefer pass/fail or small scales.** A 1–5 scale is easier to keep consistent than 1–100.

### Pairwise comparison

Often the real question is "is the new prompt better than the old one?" Judges are better at **comparing** two answers than scoring one in isolation. But they have **position bias**: a tendency to prefer whichever answer comes first. Fix it by asking twice with the order swapped, and only counting a win when both orders agree:

```python
def pairwise(client, question, a, b):
    one = prefer(client, question, first=a, second=b)        # "first" | "second" | "tie"
    two = prefer(client, question, first=b, second=a)
    one = {"first": "A", "second": "B", "tie": "tie"}[one]
    two = {"first": "B", "second": "A", "tie": "tie"}[two]
    return one if one == two else "tie"
```

Run it across your dataset and report a win rate: "new prompt wins 34, loses 9, ties 7".

> **Note:** LLM judges cost money and add their own noise. Use code checks for everything code can check, and the judge only for what's left.

## 5. Run evals on every change

Evals are only useful if they run when things change:

- **Every prompt change.** Prompts are code. A one-word change can flip outcomes.
- **Every model change.** Moving from Opus to Sonnet to save money? The eval tells you what that costs in quality. Run the same set on both and compare pass rate **and** cost per case.
- **Every tool or retrieval change.**
- **In CI.** A test that fails if the pass rate drops below a threshold:

```python
# tests/test_evals.py: run with `pytest -m evals` (it calls the real API, so keep it out of the fast suite)
import json

import pytest

from app.agent import answer
from evals.runner import run_evals


@pytest.mark.evals
def test_pass_rate_does_not_regress():
    cases = json.load(open("evals/golden.json"))
    report = run_evals(answer, cases)
    assert report["pass_rate"] >= 0.85, f"pass rate {report['pass_rate']:.0%}; failures: {report['failures']}"
```

Because outputs vary between runs, a case that passes 4 times out of 5 is flaky, not fixed. For important cases, run each one 3–5 times and report the pass rate per case.

### Track scores over time

Save every eval run so you can see trends and compare versions:

```python
import json
import subprocess
from datetime import datetime, timezone


def record(report: dict, prompt_version: str, model: str, path="evals/history.jsonl"):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    row = {"at": datetime.now(timezone.utc).isoformat(), "commit": commit, "prompt": prompt_version,
           "model": model, **report}
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")
```

A JSON-lines file is enough to start. When you change something, you can now answer "did this help?" with a number and a diff of which cases flipped.

## 6. Evaluating agents: check the final state

For agents, the final text is the least reliable thing to grade. An agent can say "I've refunded your order" without calling the refund tool, or call it with the wrong amount and then describe it correctly. Grade what **happened**:

- **Final state of the world.** After the run, query the (test) database: is order A1 marked refunded, with amount 40? Is there exactly one draft reply in the queue?
- **Tool calls.** Which tools were called, with what arguments, and which were **not** called.
- **Efficiency.** Number of turns, tokens and cost. An agent that solves the task in 4 turns beats one that takes 19.
- **The text, last.** A rubric-based judge for tone and accuracy of what the user sees.

```python
def eval_refund_case(client):
    db = make_test_db(orders=[{"id": "A1", "total": 40, "status": "delivered"}])
    result = run_agent(client, "My order A1 arrived broken, I want my money back.",
                       tools=TOOLS, handlers=make_handlers(db), max_turns=8)
    order = db.get_order("A1")
    checks = {
        "refund_drafted": db.pending_refunds() == [("A1", 40)],          # final state
        "no_extra_refunds": len(db.pending_refunds()) == 1,
        "looked_up_order": any(c["name"] == "get_order" for c in result["tool_calls"]),
        "status_unchanged_until_approved": order["status"] == "delivered",
        "turns_ok": result["turns"] <= 6,
    }
    return all(checks.values()), checks
```

Each agent case sets up a fresh environment (a test database, fake external APIs), runs the agent, then inspects the environment. That's more work than grading text, and it's the only way to know the agent actually does the job.

> **Try it:** In the practice editor, build `run_evals` with the four check types, then the LLM judge with the position-swapped `pairwise` comparison.

## Common mistakes

- **No evals at all**, so every prompt change is a guess.
- **Only happy-path cases.** Add every bug you fix and every edge case you think of.
- **Using an LLM judge where code would do**, paying for noise.
- **Vague rubrics**, and judges never checked against human grades.
- **Ignoring position bias** in pairwise comparisons.
- **Trusting one run** of a flaky case.
- **Grading an agent's words instead of its actions** and the resulting state.
- **Looking at the pass rate but never reading the failures.**

## Recap

- An eval is a dataset, a task, graders and a report; you track a score, not perfection.
- Build a golden set from real inputs, past failures and edge cases; tag by category; start with 20–50.
- Grade with code first: exact, contains, JSON schema, tool-call assertions.
- Use LLM-as-judge with a specific rubric, reasoning-first structured output and calibration against humans; swap order in pairwise comparisons.
- Run evals on every prompt, model and tool change, in CI, and record scores over time.
- Evaluate agents by the final state and their tool calls, not just their final message.
