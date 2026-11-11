# An eval gate for CI

In CI, a step fails when its command exits with a nonzero code. Turn your eval results into that exit code so a prompt change that breaks quality can't be merged.

Write four functions:

```python
def run_suite(cases: list[dict], answer: Callable[[str], str]) -> list[dict]: ...
def pass_rate(results: list[dict]) -> float: ...
def eval_gate(results: list[dict], threshold: float) -> int: ...
def main(argv: list[str]) -> int: ...
```

1. **`run_suite`**: each case is `{"id", "input", "expected"}`. Call `answer(case["input"])`; the case passes if `expected` appears in the output, ignoring case. Return `[{"id": ..., "passed": bool, "output": ...}, ...]` in order. (In your project `answer` calls your app with a fake or a cheap model; here it's any function.)
2. **`pass_rate`**: the fraction that passed; `0.0` for an empty list.
3. **`eval_gate`**: return `0` if `pass_rate >= threshold`, otherwise `1`.
   - Empty results return `1`: if nothing ran, something is broken.
   - A threshold outside `0..1` raises `ValueError` (catches `90` typed instead of `0.9`).
4. **`main(["results.json", "0.9"])`**: load the JSON list from the file and print one summary line, then a line for each failed id. Return the gate's exit code:

```
pass rate 3/4 = 75.0% (threshold 90.0%) FAIL
  failed: c1
```

The `if __name__ == "__main__":` block calls `sys.exit(main(sys.argv[1:]))`, which is how CI uses it: `uv run python evals/gate.py results.json 0.9`.

## Example

```python
r = [{"id": "a", "passed": True}, {"id": "b", "passed": False}]
pass_rate(r)        # 0.5
eval_gate(r, 0.5)   # 0
eval_gate(r, 0.8)   # 1
```
