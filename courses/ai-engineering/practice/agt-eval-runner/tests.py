from solution import check, run_evals


def case(kind, expected):
    return {"id": "c", "input": None, "check": kind, "expected": expected}


def test_exact_and_contains():
    assert check(case("exact", "Paris"), "  Paris\n") is True, "exact should ignore surrounding whitespace"
    assert check(case("exact", "Paris"), "paris") is False, "exact is case-sensitive"
    assert check(case("contains", ["refund", "5 days"]), "Your REFUND arrives in 5 days.") is True, \
        "contains should ignore case"
    assert check(case("contains", ["refund", "5 days"]), "Your refund is coming.") is False, \
        "contains needs every expected string"


def test_json_keys_handles_bad_json():
    assert check(case("json_keys", ["name", "total"]), '{"name": "Ada", "total": 3, "x": 1}') is True
    assert check(case("json_keys", ["name", "total"]), '{"name": "Ada"}') is False, "a missing key should fail"
    assert check(case("json_keys", ["name"]), "Sure! Here's the JSON: {") is False, "invalid JSON should fail, not crash"
    assert check(case("json_keys", ["name"]), '["name"]') is False, "a JSON list isn't an object"


def test_tool_called_matches_name_and_input_subset():
    calls = [{"name": "get_order", "input": {"order_id": "A1"}},
             {"name": "refund", "input": {"order_id": "A1", "amount": 20, "reason": "late"}}]
    want = {"name": "refund", "input": {"order_id": "A1", "amount": 20}}
    assert check(case("tool_called", want), calls) is True, "extra input keys are fine"
    wrong = {"name": "refund", "input": {"order_id": "B2"}}
    assert check(case("tool_called", wrong), calls) is False, "a different input value should fail"
    assert check(case("tool_called", want), "I refunded it!") is False, "text isn't a list of tool calls"


def test_unknown_check_raises():
    try:
        check(case("vibes", None), "anything")
    except ValueError:
        return
    raise AssertionError("an unknown check type should raise ValueError")


def test_run_evals_reports_pass_rate_and_crashes_fail():
    def agent(text):
        if text == "boom":
            raise RuntimeError("tool exploded")
        return f"Hello {text}"

    cases = [
        {"id": "a", "input": "Ada", "check": "contains", "expected": ["hello", "ada"]},
        {"id": "b", "input": "Bo", "check": "exact", "expected": "Hello Bo"},
        {"id": "c", "input": "boom", "check": "contains", "expected": ["hello"]},
        {"id": "d", "input": "Cy", "check": "exact", "expected": "Hi Cy"},
    ]
    got = run_evals(agent, cases)
    want = {"total": 4, "passed": 2, "pass_rate": 0.5, "failures": ["c", "d"]}
    assert got == want, f"expected {want!r}, got {got!r}"
    empty = run_evals(agent, [])
    assert empty == {"total": 0, "passed": 0, "pass_rate": 0.0, "failures": []}, f"got {empty!r}"
