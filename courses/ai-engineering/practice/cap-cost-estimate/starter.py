def estimate_monthly_cost(users: int, msgs_per_user: int, in_tokens: int, out_tokens: int,
                          prices: dict[str, float]) -> float:
    """Monthly LLM cost in dollars, rounded to cents. prices are dollars per million tokens."""
    # TODO: raise ValueError if any count is negative
    # TODO: messages · (in_tokens · input price + out_tokens · output price) / 1_000_000, rounded to 2 places
    return 0.0


def pick_model(budget: float, users: int, msgs_per_user: int, in_tokens: int, out_tokens: int,
               models: dict[str, dict[str, float]]) -> str | None:
    """The first (best) model in `models` whose monthly cost is within budget, or None."""
    # TODO
    return None


if __name__ == "__main__":
    OPUS = {"input": 4.0, "output": 20.0}
    SONNET = {"input": 2.0, "output": 10.0}
    HAIKU = {"input": 0.10, "output": 0.50}
    print(estimate_monthly_cost(50, 200, 3000, 400, OPUS))   # want 200.0
    print(estimate_monthly_cost(50, 200, 3000, 400, HAIKU))  # want 5.0
    models = {"claude-opus-5-5": OPUS, "claude-sonnet-5-5": SONNET, "claude-haiku-5-5": HAIKU}
    print(pick_model(150, 50, 200, 3000, 400, models))       # want 'claude-sonnet-5-5'
