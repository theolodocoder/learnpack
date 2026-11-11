PRICES: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def cost_usd(model: str, usage) -> float:
    """Dollar cost of one response, from its usage."""
    if model not in PRICES:
        raise ValueError(f"no price for model {model!r}")
    input_price, output_price = PRICES[model]
    return (usage.input_tokens * input_price + usage.output_tokens * output_price) / 1_000_000
