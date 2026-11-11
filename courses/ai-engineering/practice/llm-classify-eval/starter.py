import re

LABELS = ("positive", "negative", "neutral")

SYSTEM = """TODO: explain the task, list the three labels, and ask for the answer in <label></label> tags."""


def classify_sentiment(client, review: str, model: str = "claude-opus-5-5") -> str:
    """Return 'positive', 'negative', 'neutral', or 'unknown'."""
    # TODO: call client.messages.create with model, max_tokens, system=SYSTEM and the review in <review> tags
    # TODO: join the text blocks of the reply
    # TODO: pull out the text between <label> and </label> (re.search is handy), strip + lowercase
    # TODO: return it if it's in LABELS, else "unknown"
    raise NotImplementedError


def evaluate(client, cases: list[tuple[str, str]], model: str = "claude-opus-5-5") -> float:
    """Fraction of (review, expected_label) cases classified correctly."""
    # TODO
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    cases = [
        ("Arrived fast and works perfectly.", "positive"),
        ("Stopped charging after two days.", "negative"),
        ("It is a phone case. It fits the phone.", "neutral"),
    ]
    try:
        print(evaluate(anthropic.Anthropic(), cases, model="claude-haiku-5-5"))
    except NotImplementedError:
        print("Write classify_sentiment and evaluate first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
