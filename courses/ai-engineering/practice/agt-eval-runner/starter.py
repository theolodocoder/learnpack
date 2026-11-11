import json


def check(case: dict, output) -> bool:
    """Grade one output against one case's check."""
    kind, expected = case["check"], case["expected"]
    # TODO: "exact", "contains", "json_keys", "tool_called" (see the table)
    # TODO: unknown kind -> raise ValueError
    raise NotImplementedError


def run_evals(fn, cases: list[dict]) -> dict:
    """Run fn on every case's input and report the pass rate."""
    # TODO: for each case: output = fn(case["input"]); a raised exception counts as a failure
    # TODO: return {"total", "passed", "pass_rate", "failures"}
    raise NotImplementedError


if __name__ == "__main__":
    def toy_agent(text):
        if "refund" in text:
            return [{"name": "refund", "input": {"order_id": text.split()[-1], "reason": "customer asked"}}]
        return "Hello! How can I help?"

    cases = [
        {"id": "greet", "input": "hi", "check": "contains", "expected": ["hello"]},
        {"id": "refund", "input": "refund A1", "check": "tool_called",
         "expected": {"name": "refund", "input": {"order_id": "A1"}}},
        {"id": "exact", "input": "hi", "check": "exact", "expected": "Hi"},
    ]
    try:
        print(run_evals(toy_agent, cases))
    except NotImplementedError:
        print("Write check and run_evals first, then Run again.")
