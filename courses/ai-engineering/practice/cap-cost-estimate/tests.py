from solution import estimate_monthly_cost, pick_model

OPUS = {"input": 4.0, "output": 20.0}
SONNET = {"input": 2.0, "output": 10.0}
HAIKU = {"input": 0.10, "output": 0.50}
MODELS = {"claude-opus-5-5": OPUS, "claude-sonnet-5-5": SONNET, "claude-haiku-5-5": HAIKU}


def test_cost_for_opus_and_haiku():
    got = estimate_monthly_cost(50, 200, 3000, 400, OPUS)
    assert got == 200.0, f"expected 200.0, got {got!r}"
    got = estimate_monthly_cost(50, 200, 3000, 400, HAIKU)
    assert got == 5.0, f"expected 5.0, got {got!r}"


def test_rounds_to_cents():
    got = estimate_monthly_cost(3, 10, 1234, 321, HAIKU)
    # 30 messages · (1234·0.10 + 321·0.50) / 1e6 = 0.0085...
    assert got == 0.01, f"expected 0.01 (rounded to cents), got {got!r}"


def test_zero_users_costs_nothing():
    got = estimate_monthly_cost(0, 200, 3000, 400, OPUS)
    assert got == 0.0, f"expected 0.0, got {got!r}"


def test_negative_counts_raise_value_error():
    for args in [(-1, 1, 1, 1), (1, -1, 1, 1), (1, 1, -1, 1), (1, 1, 1, -1)]:
        try:
            estimate_monthly_cost(*args, OPUS)
        except ValueError:
            continue
        raise AssertionError(f"estimate_monthly_cost{args} should raise ValueError")


def test_pick_model_takes_the_best_that_fits():
    got = pick_model(150, 50, 200, 3000, 400, MODELS)
    assert got == "claude-sonnet-5-5", f"Opus costs $200 and Sonnet $100: expected 'claude-sonnet-5-5', got {got!r}"
    got = pick_model(200, 50, 200, 3000, 400, MODELS)
    assert got == "claude-opus-5-5", f"a budget exactly equal to the cost fits: expected 'claude-opus-5-5', got {got!r}"


def test_pick_model_returns_none_when_nothing_fits():
    got = pick_model(1, 50, 200, 3000, 400, MODELS)
    assert got is None, f"even Haiku costs $5: expected None, got {got!r}"
