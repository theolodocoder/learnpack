from datetime import date

PRICES = {  # dollars per 1M tokens: (input, output)
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


class CostTracker:
    def __init__(self):
        self.requests = 0
        # TODO: somewhere to store costs per day

    def record(self, model: str, usage, day: date) -> float:
        """Store the cost of one call and return it."""
        # TODO: raise ValueError for an unknown model
        # TODO: compute the cost, store it under `day`, count the request, return the cost
        raise NotImplementedError

    def total(self) -> float:
        # TODO
        raise NotImplementedError

    def by_day(self) -> dict[date, float]:
        # TODO
        raise NotImplementedError


if __name__ == "__main__":
    from types import SimpleNamespace as U

    t = CostTracker()
    try:
        t.record("claude-opus-5-5", U(input_tokens=1_000, output_tokens=1_000), date(2026, 11, 10))
        t.record("claude-haiku-5-5", U(input_tokens=10_000, output_tokens=2_000), date(2026, 11, 11))
        print(t.total(), t.by_day(), t.requests)
    except NotImplementedError:
        print("Fill in the TODOs, then Run again.")
