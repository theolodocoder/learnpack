def estimate_monthly_cost(users: int, msgs_per_user: int, in_tokens: int, out_tokens: int,
                          prices: dict[str, float]) -> float:
    """Monthly LLM cost in dollars, rounded to cents. prices are dollars per million tokens."""
    if min(users, msgs_per_user, in_tokens, out_tokens) < 0:
        raise ValueError("counts must not be negative")
    messages = users * msgs_per_user
    per_message = (in_tokens * prices["input"] + out_tokens * prices["output"]) / 1_000_000
    return round(messages * per_message, 2)


def pick_model(budget: float, users: int, msgs_per_user: int, in_tokens: int, out_tokens: int,
               models: dict[str, dict[str, float]]) -> str | None:
    """The first (best) model in `models` whose monthly cost is within budget, or None."""
    for name, prices in models.items():
        if estimate_monthly_cost(users, msgs_per_user, in_tokens, out_tokens, prices) <= budget:
            return name
    return None


if __name__ == "__main__":
    print(estimate_monthly_cost(50, 200, 3000, 400, {"input": 4.0, "output": 20.0}))
