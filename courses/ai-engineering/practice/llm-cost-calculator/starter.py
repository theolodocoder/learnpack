PRICES: dict[str, tuple[float, float]] = {
    # TODO: "model-id": (input price per 1M tokens, output price per 1M tokens)
}


def cost_usd(model: str, usage) -> float:
    """Dollar cost of one response, from its usage."""
    # TODO: look up the prices (raise ValueError for an unknown model)
    # TODO: return the input cost plus the output cost
    raise NotImplementedError


if __name__ == "__main__":
    from types import SimpleNamespace

    try:
        print(cost_usd("claude-opus-5-5", SimpleNamespace(input_tokens=2_000, output_tokens=500)))  # 0.018
    except NotImplementedError:
        print("Fill in the TODOs, then Run again.")
