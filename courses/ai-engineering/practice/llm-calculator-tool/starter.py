CALCULATOR_TOOL: dict = {
    "name": "calculator",
    # TODO: "description", "strict", "input_schema"
}


def run_calculator(tool_input: dict) -> str:
    """Validate the tool input, do the arithmetic, return the result as a string."""
    # TODO: check operation is one of add/subtract/multiply/divide
    # TODO: check a and b are int or float but not bool
    # TODO: refuse division by zero
    # TODO: compute and return str(result)
    raise NotImplementedError


if __name__ == "__main__":
    try:
        print(run_calculator({"operation": "multiply", "a": 3, "b": 4}))  # 12
        print(run_calculator({"operation": "divide", "a": 7, "b": 2}))    # 3.5
    except NotImplementedError:
        print("Fill in the TODOs, then Run again.")
