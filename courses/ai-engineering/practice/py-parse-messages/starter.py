from dataclasses import dataclass

ROLES = {"user", "assistant"}


@dataclass
class Message:
    role: str
    content: str


def parse_messages(raw: list[dict]) -> list[Message]:
    """Keep only well-formed user/assistant messages, with content stripped."""
    messages: list[Message] = []
    # TODO: for each item, skip it if role/content is missing, role not in ROLES,
    #       or content is blank after .strip(); otherwise append a Message.
    return messages


def transcript(messages: list[Message]) -> str:
    """One 'role: content' line per message."""
    # TODO: build the lines (an f-string in a comprehension works well) and join them
    return ""


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
