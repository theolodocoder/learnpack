# A tool registry built from Python functions

Writing JSON schemas by hand for every tool is tedious and drifts out of sync with the code. Build a small registry whose `@registry.tool` decorator reads a function's type hints and docstring and generates the tool definition for you.

```python
class ToolRegistry:
    def tool(self, fn): ...                  # decorator: registers fn, returns fn unchanged
    def schemas(self) -> list[dict]: ...      # tool definitions, in registration order
    def call(self, name: str, input: dict) -> str: ...
```

## The schema for one function

- `"name"`: the function's `__name__`.
- `"description"`: the docstring's first paragraph (everything before the first blank line), from `inspect.getdoc(fn)`. No docstring → `""`.
- `"input_schema"`: `{"type": "object", "properties": {...}, "required": [...], "additionalProperties": False}`.
  - One property per parameter. Map types with `typing.get_type_hints(fn)`:
    `str` → `{"type": "string"}`, `int` → `"integer"`, `float` → `"number"`, `bool` → `"boolean"`,
    `Literal["a", "b"]` → `{"type": "string", "enum": ["a", "b"]}`.
  - A parameter with no type hint, or any other type, raises `TypeError` when the function is decorated.
  - Parameters **without** a default go in `"required"` (in signature order).
  - If the docstring has an `Args:` section with lines like `city: City name, e.g. Lagos.`, use the text after the colon as that property's `"description"`.

## Calling a tool

`call(name, input)` runs the registered function with `**input` and returns `str(result)`. An unknown name raises `KeyError`.

## Example

```python
registry = ToolRegistry()

@registry.tool
def get_weather(city: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
    """Get the current weather for a city.

    Args:
        city: City name, e.g. Lagos.
        unit: Temperature unit.
    """
    return f"31 degrees in {city}"

registry.schemas()
# [{"name": "get_weather",
#   "description": "Get the current weather for a city.",
#   "input_schema": {"type": "object",
#       "properties": {"city": {"type": "string", "description": "City name, e.g. Lagos."},
#                      "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit."}},
#       "required": ["city"], "additionalProperties": False}}]
registry.call("get_weather", {"city": "Lagos"})   # "31 degrees in Lagos"
```
