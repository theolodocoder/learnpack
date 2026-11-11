from collections import defaultdict
from datetime import date

PRICES = {  # dollars per 1M tokens: (input, output)
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


class CostTracker:
    def __init__(self):
        self.requests = 0
        self._daily: defaultdict[date, float] = defaultdict(float)

    def record(self, model: str, usage, day: date) -> float:
        """Store the cost of one call and return it."""
        if model not in PRICES:
            raise ValueError(f"no price for model {model!r}")
        input_price, output_price = PRICES[model]
        cost = (usage.input_tokens * input_price + usage.output_tokens * output_price) / 1_000_000
        self._daily[day] += cost
        self.requests += 1
        return cost

    def total(self) -> float:
        return sum(self._daily.values())

    def by_day(self) -> dict[date, float]:
        return dict(self._daily)
