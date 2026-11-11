# Define a calculator tool, and don't trust its input

Language models are bad at exact arithmetic. Give Claude a calculator.

Write:

```python
CALCULATOR_TOOL: dict

def run_calculator(tool_input: dict) -> str: ...
```

## `CALCULATOR_TOOL`

A tool definition with:

- `"name": "calculator"` and a helpful `"description"` (say what it does and when to use it)
- `"strict": True`
- an `"input_schema"` for an object with `operation` (string, enum `"add"`, `"subtract"`, `"multiply"`, `"divide"`), `a` (number) and `b` (number). All three are `required`, and `"additionalProperties": False`.

## `run_calculator`

This runs when Claude calls the tool. Treat the input like data from an HTTP request: check it.

- Raise `ValueError` if `operation` isn't one of the four, or if `a` or `b` isn't an `int` or `float` (note: `True` is an `int` in Python; reject `bool`s too).
- Raise `ValueError` for division by zero.
- Otherwise return the result as a string with `str(...)`.

## Example

```python
run_calculator({"operation": "multiply", "a": 3, "b": 4})   # "12"
run_calculator({"operation": "divide", "a": 7, "b": 2})     # "3.5"
run_calculator({"operation": "divide", "a": 1, "b": 0})     # ValueError
run_calculator({"operation": "add", "a": "2", "b": 2})      # ValueError
```
