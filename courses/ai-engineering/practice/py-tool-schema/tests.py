from solution import WeatherInput, make_tool


def _tool():
    return make_tool("get_weather", "Get the forecast.", WeatherInput)


def test_tool_has_exactly_name_description_and_input_schema():
    tool = _tool()
    assert set(tool) == {"name", "description", "input_schema"}, f"unexpected keys: {sorted(tool)!r}"
    assert tool["name"] == "get_weather" and tool["description"] == "Get the forecast.", f"got {tool!r}"


def test_only_city_is_required():
    schema = _tool()["input_schema"]
    assert schema.get("required") == ["city"], f"expected required ['city'], got {schema.get('required')!r}"
    assert set(schema["properties"]) == {"city", "unit", "days"}, f"got properties {sorted(schema['properties'])!r}"


def test_city_has_a_description():
    city = _tool()["input_schema"]["properties"]["city"]
    assert city.get("description"), f"city should have a description, got {city!r}"


def test_unit_is_an_enum_with_celsius_default():
    unit = _tool()["input_schema"]["properties"]["unit"]
    assert unit.get("enum") == ["celsius", "fahrenheit"], f"expected enum, got {unit!r}"
    assert unit.get("default") == "celsius", f"expected default 'celsius', got {unit!r}"


def test_days_is_limited_to_one_through_seven():
    days = _tool()["input_schema"]["properties"]["days"]
    assert days.get("minimum") == 1 and days.get("maximum") == 7, f"expected minimum 1 / maximum 7, got {days!r}"
    assert WeatherInput(city="Lagos").days == 1, "days should default to 1"
