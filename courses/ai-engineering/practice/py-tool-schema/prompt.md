# Turn a Pydantic model into a tool definition

When you give Claude a tool, you describe its input with a JSON Schema. Writing that schema by hand is error-prone; generating it from a Pydantic model is not.

Write a model and a function:

```python
class WeatherInput(BaseModel):
    city: str                                  # required, with a description
    unit: Literal["celsius", "fahrenheit"]     # defaults to "celsius"
    days: int                                  # 1 to 7 inclusive, defaults to 1

def make_tool(name: str, description: str, model: type[BaseModel]) -> dict:
```

- Give `city` a `description` with `Field(description=...)`.
- `make_tool` returns a dict with exactly three keys: `"name"`, `"description"` and `"input_schema"`, where `input_schema` is `model.model_json_schema()`.

Example:

```python
tool = make_tool("get_weather", "Get the forecast for a city.", WeatherInput)
tool["input_schema"]["required"]                       # ['city']
tool["input_schema"]["properties"]["unit"]["enum"]     # ['celsius', 'fahrenheit']
```

This dict is exactly the shape that goes into `tools=[...]` when you call Claude, which you'll do in the next section.
