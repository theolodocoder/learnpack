# A production-grade agent loop

You wrote a basic tool loop in *Tool calling*. Real agents need to handle **every** way a turn can end, record what they did, and stop on a budget instead of crashing. Write:

```python
def run_agent(client, task: str, tools: list[dict], handlers: dict, *,
              model: str = "claude-opus-5-5", max_turns: int = 10, max_tokens: int = 4096) -> dict: ...
```

`handlers` maps a tool name to a function that takes the tool's input `dict` and returns a string. Start with `messages = [{"role": "user", "content": task}]`. Each API call is one **turn**: call `client.messages.create(model=model, max_tokens=..., tools=tools, messages=messages)`, then branch on `response.stop_reason`:

| `stop_reason` | What to do |
|---|---|
| `"end_turn"` (or anything not listed) | Finish with status `"done"`. |
| `"tool_use"` | Append the assistant turn. Run **every** `tool_use` block, and append **one** user message with all the `tool_result` blocks. A handler that raises, or an unknown tool name, gives a result with `"is_error": True` and the error message as `content`. |
| `"pause_turn"` | The server paused a long turn. Append the assistant turn **as is** and call again (no new user message). |
| `"max_tokens"` | If the **last** content block is a `tool_use` (it was cut off mid-call), retry the same messages with `max_tokens` doubled. Otherwise finish with status `"truncated"`. |
| `"refusal"` | Finish with status `"refused"`. Don't retry. |

If you've made `max_turns` calls without finishing, stop with status `"max_turns"`. Don't raise: the caller decides what to do.

Return a dict:

```python
{
    "status": "done",          # "done" | "truncated" | "refused" | "max_turns"
    "text": "...",             # text blocks of the last response, joined ("" for max_turns)
    "turns": 2,                # number of API calls made
    "tool_calls": [            # one entry per tool call, in order
        {"name": "get_weather", "input": {"city": "Lagos"}, "is_error": False},
    ],
}
```

**Check is free and offline.** **Run** uses the real API if your key is set.
