import json
import sys
from collections.abc import Callable
from pathlib import Path


def run_suite(cases: list[dict], answer: Callable[[str], str]) -> list[dict]:
    """Run each case's "input" through `answer`.

    Return [{"id", "passed", "output"}, ...]: passed if case["expected"] appears in the
    output, ignoring case.
    """
    # TODO
    return []


def pass_rate(results: list[dict]) -> float:
    # TODO: fraction of results with passed=True; 0.0 for an empty list
    return 0.0


def eval_gate(results: list[dict], threshold: float) -> int:
    """Return 0 if pass_rate >= threshold, else 1. Empty results -> 1.

    Raise ValueError if threshold isn't between 0 and 1.
    """
    # TODO
    return 1


def main(argv: list[str]) -> int:
    """argv = [path_to_results_json, threshold]. Print a summary and return the exit code."""
    # TODO: load the JSON list, print "pass rate 3/4 = 75.0% (threshold 90.0%) FAIL"
    #       then one "  failed: <id>" line per failed case, and return eval_gate(...)
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 3:
        sys.exit(main(sys.argv[1:]))
    cases = [{"id": "capital", "input": "Capital of France?", "expected": "Paris"},
             {"id": "sum", "input": "2 + 2?", "expected": "4"}]
    results = run_suite(cases, lambda q: "Paris" if "France" in q else "five")
    print(results, "gate exit code:", eval_gate(results, 0.9))
