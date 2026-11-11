def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def outline_then_draft(client, topic: str, model: str = "claude-opus-5-5") -> dict:
    """Outline a topic, check the outline in code, then draft an article from it."""
    first = client.messages.create(
        model=model,
        max_tokens=2000,
        system="You plan short technical articles.",
        messages=[{"role": "user", "content": (
            f"<topic>{topic}</topic>\n\nWrite a bullet outline for a short article on this topic. "
            "Put each point on its own line starting with '- '. Output only the outline."
        )}],
    )
    outline = _text(first)
    bullets = [line for line in outline.splitlines() if line.lstrip().startswith("- ")]
    if len(bullets) < 3:
        raise ValueError(f"outline has {len(bullets)} bullet points; need at least 3")

    second = client.messages.create(
        model=model,
        max_tokens=8000,
        system="You write clear, concise technical articles.",
        messages=[{"role": "user", "content": (
            f"<outline>\n{outline}\n</outline>\n\nWrite a short article that follows this outline point by point."
        )}],
    )
    return {"outline": outline, "draft": _text(second)}
