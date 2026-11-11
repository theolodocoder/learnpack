from typing import Literal

from solution import ToolRegistry


def make():
    registry = ToolRegistry()

    @registry.tool
    def get_weather(city: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
        """Get the current weather for a city.

        Uses a cached forecast.

        Args:
            city: City name, e.g. Lagos.
            unit: Temperature unit.
        """
        return f"31 degrees in {city} ({unit})"

    @registry.tool
    def add(a: int, b: float, exact: bool = True):
        return a + b

    return registry, get_weather


def test_decorator_returns_the_function():
    _, get_weather = make()
    assert callable(get_weather) and get_weather("Accra") == "31 degrees in Accra (celsius)", \
        "the decorator must return the original function unchanged"


def test_schema_name_description_and_required():
    registry, _ = make()
    schemas = registry.schemas()
    assert [s["name"] for s in schemas] == ["get_weather", "add"], f"expected both tools in order, got {schemas!r}"
    s = schemas[0]
    assert s["description"] == "Get the current weather for a city.", \
        f"description should be the docstring's first paragraph, got {s['description']!r}"
    inp = s["input_schema"]
    assert inp["type"] == "object" and inp["additionalProperties"] is False, "input_schema needs type object and additionalProperties False"
    assert inp["required"] == ["city"], f"only parameters without defaults are required, got {inp['required']!r}"


def test_types_literal_and_arg_descriptions():
    registry, _ = make()
    weather, add = registry.schemas()
    props = weather["input_schema"]["properties"]
    want_city = {"type": "string", "description": "City name, e.g. Lagos."}
    assert props["city"] == want_city, f"expected {want_city!r}, got {props['city']!r}"
    want_unit = {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit."}
    assert props["unit"] == want_unit, f"expected {want_unit!r}, got {props['unit']!r}"
    want = {"a": {"type": "integer"}, "b": {"type": "number"}, "exact": {"type": "boolean"}}
    got = add["input_schema"]["properties"]
    assert got == want, f"expected {want!r}, got {got!r}"
    assert add["description"] == "", f"no docstring should give an empty description, got {add['description']!r}"


def test_missing_or_unsupported_hint_raises_type_error():
    registry = ToolRegistry()
    for bad in ("def f(x): pass", "def f(x: dict): pass"):
        ns = {}
        exec(bad, ns)
        try:
            registry.tool(ns["f"])
        except TypeError:
            continue
        raise AssertionError(f"expected TypeError when decorating `{bad}`")


def test_call_runs_tool_and_returns_string():
    registry, _ = make()
    got = registry.call("get_weather", {"city": "Lagos", "unit": "fahrenheit"})
    assert got == "31 degrees in Lagos (fahrenheit)", f"got {got!r}"
    got = registry.call("add", {"a": 2, "b": 0.5})
    assert got == "2.5", f"call should return str(result), got {got!r}"
    try:
        registry.call("launch_rocket", {})
    except KeyError:
        return
    raise AssertionError("an unknown tool name should raise KeyError")
