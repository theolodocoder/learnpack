ROUTES = {
    "billing": "You are a billing specialist. Explain charges, refunds and invoices precisely. Never promise a refund; say a human will confirm it.",
    "technical": "You are a technical support engineer. Ask for error messages and versions, then give numbered troubleshooting steps.",
    "general": "You are a friendly customer support agent. Answer briefly and point to the right team when unsure.",
}


def route(client, message: str, router_model: str = "claude-haiku-5-5",
          model: str = "claude-opus-5-5") -> tuple[str, str]:
    """Classify the message with a cheap model, then answer it with the matching specialist prompt."""
    # TODO: call 1 with router_model: system lists the categories, asks for <category>...</category>;
    #       the user message wraps `message` in <message>...</message>
    # TODO: extract the category (strip + lower); fall back to "general" if missing or unknown
    # TODO: call 2 with model, system=ROUTES[category], messages=[{"role": "user", "content": message}]
    # TODO: return (category, answer_text)
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    try:
        print(route(anthropic.Anthropic(), "The app crashes when I upload a PDF", model="claude-haiku-5-5"))
    except NotImplementedError:
        print("Write route first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
