def chat_once(client, system: str, history: list[dict], user_msg: str,
              model: str = "claude-opus-5-5") -> tuple[str, list[dict]]:
    """Send one user message with the full history; return (reply_text, new_history)."""
    messages = [*history, {"role": "user", "content": user_msg}]
    response = client.messages.create(model=model, max_tokens=16000, system=system, messages=messages)
    reply = "".join(block.text for block in response.content if block.type == "text")
    return reply, [*messages, {"role": "assistant", "content": reply}]
