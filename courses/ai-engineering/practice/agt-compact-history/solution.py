SYSTEM = (
    "You compress conversations. Summarise the transcript in a few sentences. Keep every name, number, "
    "decision, preference and open question; drop small talk."
)


def compact_history(client, messages: list[dict], keep_last: int = 4,
                    model: str = "claude-haiku-5-5") -> list[dict]:
    """Replace all but the newest turns with a summary, folded into the first kept user message."""
    if len(messages) <= keep_last:
        return [dict(m) for m in messages]
    split = len(messages) - keep_last
    while split > 0 and messages[split]["role"] == "assistant":
        split -= 1
    if split <= 0:
        return [dict(m) for m in messages]

    old, recent = messages[:split], [dict(m) for m in messages[split:]]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in old)
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"<transcript>\n{transcript}\n</transcript>"}],
    )
    summary = "".join(b.text for b in response.content if b.type == "text").strip()
    recent[0]["content"] = f"<summary>\n{summary}\n</summary>\n\n{recent[0]['content']}"
    return recent
