def run_tool_loop(client, user_msg: str, tools: list[dict], handlers: dict,
                  model: str = "claude-opus-5-5", max_turns: int = 10) -> str:
    """Call Claude, run the tools it asks for, repeat until it answers. Return the final text."""
    messages = [{"role": "user", "content": user_msg}]
    for _ in range(max_turns):
        response = client.messages.create(model=model, max_tokens=16000, tools=tools, messages=messages)
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = {"type": "tool_result", "tool_use_id": block.id}
            try:
                handler = handlers[block.name]
            except KeyError:
                result |= {"content": f"unknown tool {block.name!r}", "is_error": True}
            else:
                try:
                    result["content"] = str(handler(block.input))
                except Exception as e:
                    result |= {"content": f"{type(e).__name__}: {e}", "is_error": True}
            results.append(result)
        messages.append({"role": "user", "content": results})
    raise RuntimeError(f"no final answer after {max_turns} turns")
