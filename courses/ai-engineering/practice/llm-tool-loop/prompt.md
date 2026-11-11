# The tool-calling loop

Write the loop that lets Claude use your tools:

```python
def run_tool_loop(client, user_msg: str, tools: list[dict], handlers: dict,
                  model: str = "claude-opus-5-5", max_turns: int = 10) -> str: ...
```

- `tools` is the list of tool definitions to send.
- `handlers` maps a tool name to a Python function that takes the tool's input `dict` and returns a string.

The loop:

1. Start with `messages = [{"role": "user", "content": user_msg}]`.
2. Call `client.messages.create(model=..., max_tokens=16000, tools=tools, messages=messages)`.
3. If `response.stop_reason != "tool_use"`, you're done: return the text of the reply's `text` blocks joined together.
4. Otherwise append `{"role": "assistant", "content": response.content}`, then run **every** `tool_use` block in the reply and send **all** results back in **one** user message:
   ```python
   {"role": "user", "content": [
       {"type": "tool_result", "tool_use_id": block.id, "content": "<result string>"},
       ...
   ]}
   ```
5. If a handler raises an exception, or the tool name isn't in `handlers`, don't crash: send that result with `"is_error": True` and the error message as its `content`.
6. Go back to step 2. If you've made `max_turns` calls and Claude still wants tools, raise `RuntimeError`.

## Example

```python
handlers = {"get_weather": lambda inp: f"31°C and humid in {inp['city']}"}
run_tool_loop(client, "Weather in Lagos?", [WEATHER_TOOL], handlers)
# call 1: Claude replies with tool_use get_weather {"city": "Lagos"}
# you run it and send the tool_result
# call 2: Claude replies "It's 31°C and humid in Lagos."  -> returned
```

**Check is free and offline.** **Run** uses the real API if your key is set.
