import json


def check(case: dict, output) -> bool:
    """Grade one output against one case's check."""
    kind, expected = case["check"], case["expected"]
    if kind == "exact":
        return isinstance(output, str) and output.strip() == expected
    if kind == "contains":
        return isinstance(output, str) and all(s.lower() in output.lower() for s in expected)
    if kind == "json_keys":
        try:
            data = json.loads(output)
        except (TypeError, ValueError):
            return False
        return isinstance(data, dict) and all(k in data for k in expected)
    if kind == "tool_called":
        if not isinstance(output, list):
            return False
        return any(
            call.get("name") == expected["name"]
            and all(call.get("input", {}).get(k) == v for k, v in expected.get("input", {}).items())
            for call in output
        )
    raise ValueError(f"unknown check {kind!r} in case {case.get('id')!r}")


def run_evals(fn, cases: list[dict]) -> dict:
    """Run fn on every case's input and report the pass rate."""
    failures = []
    for case in cases:
        try:
            output = fn(case["input"])
        except Exception:
            failures.append(case["id"])
            continue
        if not check(case, output):
            failures.append(case["id"])
    total = len(cases)
    passed = total - len(failures)
    return {"total": total, "passed": passed, "pass_rate": passed / total if total else 0.0, "failures": failures}
