def run_agent(client, task: str, tools: list[dict], handlers: dict, *,
              model: str = "claude-opus-5-5", max_turns: int = 10, max_tokens: int = 4096) -> dict:
    """Run the tool loop until Claude finishes, refuses, truncates, or the turn budget runs out."""
    messages = [{"role": "user", "content": task}]
    tool_calls = []
    for turn in range(1, max_turns + 1):
        # TODO: response = client.messages.create(model=model, max_tokens=max_tokens, tools=tools, messages=messages)
        # TODO: "tool_use": append the assistant turn, run every tool_use block (is_error on failure),
        #       record each in tool_calls, append ONE user message with all results, continue
        # TODO: "pause_turn": append the assistant turn and continue
        # TODO: "max_tokens": if response.content[-1] is a tool_use, double max_tokens and continue;
        #       otherwise return status "truncated"
        # TODO: "refusal": return status "refused"
        # TODO: anything else: return status "done"
        raise NotImplementedError
    return {"status": "max_turns", "text": "", "turns": max_turns, "tool_calls": tool_calls}


if __name__ == "__main__":
    import anthropic

    WEATHER_TOOL = {
        "name": "get_weather",
        "description": "Current weather for a city.",
        "input_schema": {"type": "object", "properties": {"city": {"type": "string"}},
                         "required": ["city"], "additionalProperties": False},
    }
    handlers = {"get_weather": lambda inp: f"31°C and humid in {inp['city']}"}
    try:
        result = run_agent(anthropic.Anthropic(), "Weather in Lagos and Accra?", [WEATHER_TOOL], handlers,
                           model="claude-haiku-5-5")
        print(result)
    except NotImplementedError:
        print("Write run_agent first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
