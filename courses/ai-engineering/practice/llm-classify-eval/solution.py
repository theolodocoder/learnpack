import re

LABELS = ("positive", "negative", "neutral")

SYSTEM = """You classify the sentiment of product reviews for an online shop.
Choose exactly one label:
- positive: the customer is happy with the product or service
- negative: the customer is unhappy or reports a problem
- neutral: factual, mixed, or no clear feeling
The label feeds an automated dashboard, so answer with the label inside <label></label> tags and nothing else."""


def classify_sentiment(client, review: str, model: str = "claude-opus-5-5") -> str:
    """Return 'positive', 'negative', 'neutral', or 'unknown'."""
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"<review>\n{review}\n</review>"}],
    )
    reply = "".join(b.text for b in response.content if b.type == "text")
    match = re.search(r"<label>(.*?)</label>", reply, re.DOTALL)
    if not match:
        return "unknown"
    label = match.group(1).strip().lower()
    return label if label in LABELS else "unknown"


def evaluate(client, cases: list[tuple[str, str]], model: str = "claude-opus-5-5") -> float:
    """Fraction of (review, expected_label) cases classified correctly."""
    if not cases:
        return 0.0
    correct = sum(classify_sentiment(client, review, model) == want for review, want in cases)
    return correct / len(cases)
