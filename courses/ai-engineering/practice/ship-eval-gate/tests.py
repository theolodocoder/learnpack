import contextlib
import io
import json
import os
import tempfile

from solution import eval_gate, main, pass_rate, run_suite

CASES = [
    {"id": "refund", "input": "How long do refunds take?", "expected": "5 days"},
    {"id": "hours", "input": "When are you open?", "expected": "9am"},
    {"id": "phone", "input": "Phone number?", "expected": "0800"},
    {"id": "ship", "input": "Do you ship abroad?", "expected": "yes"},
]
ANSWERS = {"refund": "Refunds take 5 DAYS.", "hours": "We open at 9AM.", "phone": "Email us.", "ship": "Yes, worldwide."}


def fake_answer(question):
    case = next(c for c in CASES if c["input"] == question)
    return ANSWERS[case["id"]]


def results_of(*flags):
    return [{"id": f"c{i}", "passed": f} for i, f in enumerate(flags)]


def test_run_suite_checks_expected_text_case_insensitively():
    results = run_suite(CASES, fake_answer)
    got = [(r["id"], r["passed"]) for r in results]
    want = [("refund", True), ("hours", True), ("phone", False), ("ship", True)]
    assert got == want, f"expected {want!r}, got {got!r}"
    assert results[0]["output"] == "Refunds take 5 DAYS.", "each result should keep the model's output for debugging"


def test_pass_rate():
    got = pass_rate(results_of(True, True, False, True))
    assert got == 0.75, f"expected 0.75, got {got!r}"
    assert pass_rate([]) == 0.0, "an empty list has a pass rate of 0.0"


def test_gate_passes_at_or_above_threshold_and_fails_below():
    r = results_of(True, True, False, True)
    for threshold, want in [(0.75, 0), (0.5, 0), (0.8, 1), (1.0, 1)]:
        got = eval_gate(r, threshold)
        assert got == want, f"pass rate 0.75, threshold {threshold}: expected exit code {want}, got {got}"


def test_empty_results_fail_and_bad_threshold_raises():
    assert eval_gate([], 0.0) == 1, "no results at all must fail the build (the eval probably didn't run)"
    for bad in (-0.1, 1.5, 90):
        try:
            eval_gate(results_of(True), bad)
        except ValueError:
            continue
        raise AssertionError(f"threshold {bad} should raise ValueError (use 0.9, not 90)")


def test_main_reads_file_prints_summary_and_returns_exit_code():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "results.json")
        with open(path, "w") as f:
            json.dump(results_of(True, False, True, True), f)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([path, "0.9"])
    printed = out.getvalue()
    assert code == 1, f"0.75 < 0.9 should return 1, got {code!r}"
    assert "3/4" in printed and "FAIL" in printed, f"summary should show '3/4' and 'FAIL', got {printed!r}"
    assert "c1" in printed, f"the failed case id should be printed, got {printed!r}"
