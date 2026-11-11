import inspect
import typing
from typing import Literal

TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}


class ToolRegistry:
    def __init__(self):
        self._tools = {}  # name -> (function, schema)

    def tool(self, fn):
        """Decorator: build fn's tool schema, register it, and return fn unchanged."""
        # TODO: hints = typing.get_type_hints(fn); params = inspect.signature(fn).parameters
        # TODO: description = first paragraph of inspect.getdoc(fn) (or "")
        # TODO: parse "name: text" lines under "Args:" into per-parameter descriptions
        # TODO: for each parameter, map its hint to a JSON schema (TypeError if missing/unsupported);
        #       typing.get_origin(hint) is Literal for Literal[...] and typing.get_args(hint) gives the values
        # TODO: parameters whose default is inspect.Parameter.empty are required
        # TODO: store (fn, schema) under fn.__name__
        return fn

    def schemas(self) -> list[dict]:
        # TODO: the schemas, in registration order
        return []

    def call(self, name: str, input: dict) -> str:
        # TODO: look up the function (KeyError if unknown), call it with **input, return str(result)
        raise NotImplementedError


if __name__ == "__main__":
    import json

    registry = ToolRegistry()

    @registry.tool
    def get_weather(city: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
        """Get the current weather for a city.

        Args:
            city: City name, e.g. Lagos.
            unit: Temperature unit.
        """
        return f"31 degrees in {city}"

    print(json.dumps(registry.schemas(), indent=2))
