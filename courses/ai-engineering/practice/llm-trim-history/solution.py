import math


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters, rounded up."""
    return math.ceil(len(text) / 4)


def trim_history(messages: list[dict], budget: int) -> list[dict]:
    """Keep the newest messages that fit in `budget` tokens; result must start with a user message."""
    kept = []
    used = 0
    for message in reversed(messages):
        cost = estimate_tokens(message["content"])
        if used + cost > budget:
            break
        kept.append(message)
        used += cost
    kept.reverse()
    while kept and kept[0]["role"] != "user":
        kept.pop(0)
    return kept
