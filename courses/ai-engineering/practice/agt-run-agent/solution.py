import logging

log = logging.getLogger("agent")


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def _run_tool(handlers: dict, block) -> dict:
    result = {"type": "tool_result", "tool_use_id": block.id}
    try:
        if block.name not in handlers:
            raise KeyError(f"unknown tool {block.name!r}")
        result["content"] = str(handlers[block.name](block.input))
    except Exception as e:
        result |= {"content": f"{type(e).__name__}: {e}", "is_error": True}
    return result


def run_agent(client, task: str, tools: list[dict], handlers: dict, *,
              model: str = "claude-opus-5-5", max_turns: int = 10, max_tokens: int = 4096) -> dict:
    """Run the tool loop until Claude finishes, refuses, truncates, or the turn budget runs out."""
    messages = [{"role": "user", "content": task}]
    tool_calls = []

    def finish(status, response, turn):
        return {"status": status, "text": _text(response), "turns": turn, "tool_calls": tool_calls}

    for turn in range(1, max_turns + 1):
        response = client.messages.create(model=model, max_tokens=max_tokens, tools=tools, messages=messages)
        reason = response.stop_reason
        log.info("turn %d: stop_reason=%s", turn, reason)

        if reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _run_tool(handlers, block)
                    tool_calls.append({"name": block.name, "input": block.input,
                                       "is_error": result.get("is_error", False)})
                    log.info("  %s(%s) -> %.80s", block.name, block.input, result["content"])
                    results.append(result)
            messages.append({"role": "user", "content": results})
        elif reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
        elif reason == "max_tokens":
            if response.content and response.content[-1].type == "tool_use":
                max_tokens *= 2  # the tool call was cut off: retry with more room
            else:
                return finish("truncated", response, turn)
        elif reason == "refusal":
            return finish("refused", response, turn)
        else:
            return finish("done", response, turn)
    return {"status": "max_turns", "text": "", "turns": max_turns, "tool_calls": tool_calls}
