import json
import sys
from collections.abc import Callable
from pathlib import Path


def run_suite(cases: list[dict], answer: Callable[[str], str]) -> list[dict]:
    """Run each case through `answer`; pass if the expected text appears (case-insensitive)."""
    results = []
    for case in cases:
        output = answer(case["input"])
        passed = case["expected"].lower() in output.lower()
        results.append({"id": case["id"], "passed": passed, "output": output})
    return results


def pass_rate(results: list[dict]) -> float:
    if not results:
        return 0.0
    return sum(r["passed"] for r in results) / len(results)


def eval_gate(results: list[dict], threshold: float) -> int:
    """0 (success) if the pass rate meets the threshold, else 1. No results is a failure."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be between 0 and 1, got {threshold}")
    if not results:
        return 1
    return 0 if pass_rate(results) >= threshold else 1


def main(argv: list[str]) -> int:
    """Usage: python eval_gate.py results.json 0.9"""
    path, threshold = argv[0], float(argv[1])
    results = json.loads(Path(path).read_text())
    passed = sum(r["passed"] for r in results)
    code = eval_gate(results, threshold)
    verdict = "PASS" if code == 0 else "FAIL"
    print(f"pass rate {passed}/{len(results)} = {pass_rate(results):.1%} (threshold {threshold:.1%}) {verdict}")
    for r in results:
        if not r["passed"]:
            print(f"  failed: {r['id']}")
    return code


if __name__ == "__main__":
    if len(sys.argv) == 3:
        sys.exit(main(sys.argv[1:]))
    cases = [{"id": "capital", "input": "Capital of France?", "expected": "Paris"},
             {"id": "sum", "input": "2 + 2?", "expected": "4"}]
    results = run_suite(cases, lambda q: "Paris" if "France" in q else "five")
    print(results, "gate exit code:", eval_gate(results, 0.9))
