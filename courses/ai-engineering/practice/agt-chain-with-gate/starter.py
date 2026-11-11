def outline_then_draft(client, topic: str, model: str = "claude-opus-5-5") -> dict:
    """Outline a topic, check the outline in code, then draft an article from it."""
    # TODO: call 1: ask for a bullet outline of <topic>{topic}</topic>, one "- " line per point
    # TODO: join the text blocks of the reply into `outline`
    # TODO: gate: count lines that start with "- " after .lstrip(); fewer than 3 -> raise ValueError
    # TODO: call 2: send the outline inside <outline>...</outline> and ask for a short article
    # TODO: return {"outline": outline, "draft": draft}
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    try:
        result = outline_then_draft(anthropic.Anthropic(), "Why every API needs a timeout", model="claude-haiku-5-5")
        print(result["outline"], "\n---\n", result["draft"])
    except NotImplementedError:
        print("Write outline_then_draft first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
