import re

ROUTES = {
    "billing": "You are a billing specialist. Explain charges, refunds and invoices precisely. Never promise a refund; say a human will confirm it.",
    "technical": "You are a technical support engineer. Ask for error messages and versions, then give numbered troubleshooting steps.",
    "general": "You are a friendly customer support agent. Answer briefly and point to the right team when unsure.",
}

ROUTER_SYSTEM = (
    "You sort customer messages into exactly one category: "
    + ", ".join(ROUTES)
    + ". Reply with the category inside <category></category> tags and nothing else."
)


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def route(client, message: str, router_model: str = "claude-haiku-5-5",
          model: str = "claude-opus-5-5") -> tuple[str, str]:
    """Classify the message with a cheap model, then answer it with the matching specialist prompt."""
    label = client.messages.create(
        model=router_model,
        max_tokens=100,
        system=ROUTER_SYSTEM,
        messages=[{"role": "user", "content": f"<message>\n{message}\n</message>"}],
    )
    m = re.search(r"<category>(.*?)</category>", _text(label), re.S)
    category = m.group(1).strip().lower() if m else ""
    if category not in ROUTES:
        category = "general"

    answer = client.messages.create(
        model=model,
        max_tokens=4000,
        system=ROUTES[category],
        messages=[{"role": "user", "content": message}],
    )
    return category, _text(answer)
