from dataclasses import dataclass

ROLES = {"user", "assistant"}


@dataclass
class Message:
    role: str
    content: str


def parse_messages(raw: list[dict]) -> list[Message]:
    """Keep only well-formed user/assistant messages, with content stripped."""
    messages: list[Message] = []
    for item in raw:
        role = item.get("role")
        content = item.get("content")
        if role not in ROLES or not isinstance(content, str) or not content.strip():
            continue
        messages.append(Message(role=role, content=content.strip()))
    return messages


def transcript(messages: list[Message]) -> str:
    """One 'role: content' line per message."""
    return "\n".join(f"{m.role}: {m.content}" for m in messages)


if __name__ == "__main__":
    raw = [
        {"role": "user", "content": "  Hi! "},
        {"role": "system", "content": "ignored"},
        {"content": "no role"},
        {"role": "assistant", "content": "Hello."},
    ]
    msgs = parse_messages(raw)
    print(msgs)
    print(transcript(msgs))
