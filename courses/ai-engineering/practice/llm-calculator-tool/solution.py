import operator

OPERATIONS = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
}

CALCULATOR_TOOL: dict = {
    "name": "calculator",
    "description": "Exact arithmetic on two numbers. Use it for any calculation instead of working it out yourself.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": list(OPERATIONS)},
            "a": {"type": "number", "description": "Left operand"},
            "b": {"type": "number", "description": "Right operand"},
        },
        "required": ["operation", "a", "b"],
        "additionalProperties": False,
    },
}


def run_calculator(tool_input: dict) -> str:
    """Validate the tool input, do the arithmetic, return the result as a string."""
    op = tool_input.get("operation")
    a, b = tool_input.get("a"), tool_input.get("b")
    if op not in OPERATIONS:
        raise ValueError(f"unknown operation {op!r}")
    for name, value in (("a", a), ("b", b)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number, got {value!r}")
    if op == "divide" and b == 0:
        raise ValueError("cannot divide by zero")
    return str(OPERATIONS[op](a, b))
