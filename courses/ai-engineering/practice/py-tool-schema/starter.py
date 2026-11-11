import json
from typing import Literal

from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    # TODO: city (required, with a description), unit (Literal, default "celsius"),
    #       days (1..7, default 1)
    pass


def make_tool(name: str, description: str, model: type[BaseModel]) -> dict:
    """Build a Claude tool definition whose input_schema comes from `model`."""
    # TODO: return {"name": ..., "description": ..., "input_schema": ...}
    raise NotImplementedError


if __name__ == "__main__":
    try:
        tool = make_tool("get_weather", "Get the forecast for a city.", WeatherInput)
        print(json.dumps(tool, indent=2))
    except NotImplementedError:
        print("Not implemented yet: fill in the TODOs, then Run again.")
