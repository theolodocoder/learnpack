def run_tool_loop(client, user_msg: str, tools: list[dict], handlers: dict,
                  model: str = "claude-opus-5-5", max_turns: int = 10) -> str:
    """Call Claude, run the tools it asks for, repeat until it answers. Return the final text."""
    messages = [{"role": "user", "content": user_msg}]
    for _ in range(max_turns):
        # TODO: response = client.messages.create(model=..., max_tokens=16000, tools=tools, messages=messages)
        # TODO: if response.stop_reason != "tool_use": return the joined text blocks
        # TODO: append the assistant turn (content=response.content)
        # TODO: for every tool_use block, run handlers[block.name](block.input)
        #       build a tool_result dict; on an exception or unknown tool use "is_error": True
        # TODO: append ONE user message with all the tool_result dicts
        raise NotImplementedError
    raise RuntimeError(f"no final answer after {max_turns} turns")


if __name__ == "__main__":
    import anthropic

    WEATHER_TOOL = {
        "name": "get_weather",
        "description": "Current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    }
    handlers = {"get_weather": lambda inp: f"31°C and humid in {inp['city']}"}
    try:
        print(run_tool_loop(anthropic.Anthropic(), "Weather in Lagos and Accra?", [WEATHER_TOOL], handlers, model="claude-haiku-5-5"))
    except NotImplementedError:
        print("Write run_tool_loop first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
