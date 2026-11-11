from solution import CALCULATOR_TOOL, run_calculator


def raises_value_error(tool_input):
    try:
        run_calculator(tool_input)
    except ValueError:
        return True
    return False


def test_tool_definition_shape():
    t = CALCULATOR_TOOL
    assert t.get("name") == "calculator", f"name should be 'calculator', got {t.get('name')!r}"
    assert len(t.get("description", "")) >= 20, "write a real description (what it does, when to use it)"
    assert t.get("strict") is True, "set \"strict\": True"
    s = t.get("input_schema", {})
    assert s.get("type") == "object" and s.get("additionalProperties") is False, "input_schema must be an object with additionalProperties False"
    assert set(s.get("required", [])) == {"operation", "a", "b"}, f"required should be operation, a, b; got {s.get('required')!r}"
    props = s.get("properties", {})
    assert set(props.get("operation", {}).get("enum", [])) == {"add", "subtract", "multiply", "divide"}, "operation needs an enum of the 4 operations"
    assert props.get("a", {}).get("type") == "number" and props.get("b", {}).get("type") == "number", "a and b should be type number"


def test_basic_operations():
    cases = [("add", 2, 3, "5"), ("subtract", 2, 3, "-1"), ("multiply", 3, 4, "12"), ("divide", 7, 2, "3.5")]
    for op, a, b, want in cases:
        got = run_calculator({"operation": op, "a": a, "b": b})
        assert got == want, f"{op}({a}, {b}): expected {want!r}, got {got!r}"


def test_division_by_zero_raises():
    assert raises_value_error({"operation": "divide", "a": 1, "b": 0}), "dividing by zero should raise ValueError"


def test_unknown_operation_raises():
    assert raises_value_error({"operation": "power", "a": 2, "b": 3}), "an unknown operation should raise ValueError"
    assert raises_value_error({"a": 2, "b": 3}), "a missing operation should raise ValueError"


def test_non_numbers_raise():
    for bad in [{"operation": "add", "a": "2", "b": 2}, {"operation": "add", "a": 2, "b": None}, {"operation": "add", "a": True, "b": 1}]:
        assert raises_value_error(bad), f"expected ValueError for {bad!r}"
