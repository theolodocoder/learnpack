import json
from typing import Literal

from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city: str = Field(description="City name, e.g. 'Lagos'")
    unit: Literal["celsius", "fahrenheit"] = "celsius"
    days: int = Field(default=1, ge=1, le=7)


def make_tool(name: str, description: str, model: type[BaseModel]) -> dict:
    """Build a Claude tool definition whose input_schema comes from `model`."""
    return {"name": name, "description": description, "input_schema": model.model_json_schema()}


if __name__ == "__main__":
    tool = make_tool("get_weather", "Get the forecast for a city.", WeatherInput)
    print(json.dumps(tool, indent=2))
