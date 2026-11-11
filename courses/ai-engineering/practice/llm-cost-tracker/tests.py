from datetime import date
from types import SimpleNamespace as U

from solution import CostTracker

D1, D2 = date(2026, 11, 10), date(2026, 11, 11)


def close(a, b):
    return abs(a - b) < 1e-9


def test_record_returns_cost_of_one_call():
    t = CostTracker()
    got = t.record("claude-opus-5-5", U(input_tokens=1_000, output_tokens=1_000), D1)
    assert close(got, 0.024), f"1k in + 1k out on Opus should cost 0.024, got {got!r}"


def test_total_and_request_count():
    t = CostTracker()
    t.record("claude-opus-5-5", U(input_tokens=1_000, output_tokens=1_000), D1)
    t.record("claude-haiku-5-5", U(input_tokens=10_000, output_tokens=2_000), D2)
    assert close(t.total(), 0.026), f"expected total 0.026, got {t.total()!r}"
    assert t.requests == 2, f"expected 2 requests, got {t.requests!r}"


def test_by_day_groups_costs():
    t = CostTracker()
    t.record("claude-sonnet-5-5", U(input_tokens=100_000, output_tokens=0), D1)   # 0.2
    t.record("claude-sonnet-5-5", U(input_tokens=0, output_tokens=10_000), D1)    # 0.1
    t.record("claude-haiku-5-5", U(input_tokens=1_000_000, output_tokens=0), D2)  # 0.1
    got = t.by_day()
    assert set(got) == {D1, D2}, f"expected keys {D1} and {D2}, got {list(got)!r}"
    assert close(got[D1], 0.3) and close(got[D2], 0.1), f"expected {{D1: 0.3, D2: 0.1}}, got {got!r}"


def test_empty_tracker():
    t = CostTracker()
    assert t.total() == 0 and t.by_day() == {} and t.requests == 0, "a new tracker should have total 0, no days, 0 requests"


def test_unknown_model_raises_and_is_not_counted():
    t = CostTracker()
    try:
        t.record("mystery-model", U(input_tokens=1, output_tokens=1), D1)
    except ValueError:
        assert t.requests == 0 and t.by_day() == {}, "a rejected call must not be counted"
        return
    raise AssertionError("expected ValueError for a model not in PRICES")
