from types import SimpleNamespace

from solution import PRICES, cost_usd


def usage(i, o):
    return SimpleNamespace(input_tokens=i, output_tokens=o)


def close(a, b):
    return abs(a - b) < 1e-9


def test_prices_table_is_correct():
    want = {"claude-opus-5-5": (4, 20), "claude-sonnet-5-5": (2, 10), "claude-haiku-5-5": (0.10, 0.50)}
    for model, (i, o) in want.items():
        got = PRICES.get(model)
        assert got is not None, f"PRICES is missing {model!r}"
        assert close(got[0], i) and close(got[1], o), f"{model}: expected ({i}, {o}), got {got!r}"


def test_opus_example():
    got = cost_usd("claude-opus-5-5", usage(2_000, 500))
    assert close(got, 0.018), f"expected 0.018, got {got!r}"


def test_one_million_tokens_each_way():
    for model, want in [("claude-opus-5-5", 24.0), ("claude-sonnet-5-5", 12.0), ("claude-haiku-5-5", 0.6)]:
        got = cost_usd(model, usage(1_000_000, 1_000_000))
        assert close(got, want), f"{model} with 1M in + 1M out: expected {want}, got {got!r}"


def test_zero_usage_costs_nothing():
    got = cost_usd("claude-haiku-5-5", usage(0, 0))
    assert got == 0, f"expected 0, got {got!r}"


def test_unknown_model_raises_value_error():
    try:
        cost_usd("gpt-imaginary", usage(10, 10))
    except ValueError:
        return
    raise AssertionError("expected ValueError for a model that isn't in PRICES")
