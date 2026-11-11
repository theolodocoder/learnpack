def build_messages(history: list[tuple[str, str]], new_message: str) -> list[dict]:
    """Turn (user, assistant) pairs plus a new user message into the API's messages list."""
    if not new_message.strip():
        raise ValueError("new_message must not be empty")
    messages = []
    for user_text, assistant_text in history:
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": assistant_text})
    messages.append({"role": "user", "content": new_message})
    return messages
