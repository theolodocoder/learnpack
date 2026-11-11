# An eval runner with code-graded checks

An eval is a test suite for an LLM feature: a fixed set of cases, a check for each, and a pass rate you track over time. Write the runner:

```python
def check(case: dict, output) -> bool: ...
def run_evals(fn, cases: list[dict]) -> dict: ...
```

Each case looks like `{"id": "refund-1", "input": ..., "check": "contains", "expected": ...}`. `fn(case["input"])` produces the output to grade.

## `check(case, output)`

| `check` | `expected` | Passes when |
|---|---|---|
| `"exact"` | a string | `output.strip() == expected` |
| `"contains"` | a list of strings | every string appears in `output`, ignoring case |
| `"json_keys"` | a list of keys | `output` parses with `json.loads` into a `dict` that has every key (bad JSON fails, it doesn't crash) |
| `"tool_called"` | `{"name": ..., "input": {...}}` | `output` is a list of tool calls (`{"name": ..., "input": {...}}`) and at least one has that name and **includes** every expected input key/value (extra keys are fine) |

An unknown `check` raises `ValueError`. That's a bug in your eval set, not a failing case.

## `run_evals(fn, cases)`

Run every case. If `fn` raises, the case fails (an agent that crashes didn't pass), and the run continues. Return:

```python
{"total": 4, "passed": 3, "pass_rate": 0.75, "failures": ["refund-2"]}
```

`failures` lists failing case ids in order. With no cases, `pass_rate` is `0.0`.

## Example

```python
cases = [
    {"id": "greet", "input": "hi", "check": "contains", "expected": ["hello"]},
    {"id": "refund", "input": "refund A1", "check": "tool_called",
     "expected": {"name": "refund", "input": {"order_id": "A1"}}},
]
run_evals(my_agent, cases)
# {"total": 2, "passed": 2, "pass_rate": 1.0, "failures": []}
```
