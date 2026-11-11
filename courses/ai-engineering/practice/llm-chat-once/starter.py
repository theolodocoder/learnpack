def chat_once(client, system: str, history: list[dict], user_msg: str,
              model: str = "claude-opus-5-5") -> tuple[str, list[dict]]:
    """Send one user message with the full history; return (reply_text, new_history)."""
    # TODO: build messages = history + the new user message (without changing `history`)
    # TODO: call client.messages.create(model=..., max_tokens=16000, system=..., messages=...)
    # TODO: join the text blocks of response.content
    # TODO: return the reply and messages + the assistant reply
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    try:
        client = anthropic.Anthropic()
        reply, history = chat_once(client, "You are terse.", [], "Capital of Nigeria?", model="claude-haiku-5-5")
        print(reply)
        reply, history = chat_once(client, "You are terse.", history, "And its population?", model="claude-haiku-5-5")
        print(reply)
    except NotImplementedError:
        print("Write chat_once first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
