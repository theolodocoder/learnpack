# Track spend per request and per day

Every serious LLM app logs what each call cost. Write a small tracker:

```python
class CostTracker:
    def record(self, model: str, usage, day: date) -> float: ...
    def total(self) -> float: ...
    def by_day(self) -> dict[date, float]: ...
    requests: int   # attribute: how many calls were recorded
```

- `PRICES` is given in the starter (dollars per 1M tokens, input and output).
- `record` works out the cost of one call from `usage.input_tokens` and `usage.output_tokens`, stores it, increments `requests`, and **returns** that call's cost. Raise `ValueError` for a model not in `PRICES` (and don't count it).
- `total()` is the sum of all recorded costs.
- `by_day()` returns a dict from each `date` to the total spent that day (only days with calls).

## Example

```python
from datetime import date
from types import SimpleNamespace as U

t = CostTracker()
t.record("claude-opus-5-5", U(input_tokens=1_000, output_tokens=1_000), date(2026, 11, 10))   # 0.024
t.record("claude-haiku-5-5", U(input_tokens=10_000, output_tokens=2_000), date(2026, 11, 11)) # 0.002
t.total()     # 0.026
t.by_day()    # {date(2026, 11, 10): 0.024, date(2026, 11, 11): 0.002}
t.requests    # 2
```
