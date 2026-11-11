# Trace every LLM call: tokens, cost, latency

Before you add a tracing service, build the core of one yourself: a wrapper that records what each Claude call cost and how long it took.

```python
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00),
          "claude-haiku-5-5": (0.10, 0.50)}   # USD per 1M tokens: (input, output)

def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None: ...

class Tracer:
    def __init__(self, clock=time.perf_counter): ...
    def create(self, client, name: str, **kwargs): ...
    def total_cost(self) -> float: ...
```

1. **`cost_usd`**: `(input_tokens × input_price + output_tokens × output_price) / 1,000,000`, rounded to 6 decimals. Unknown model → `None`.
2. **`Tracer.create(client, name, **kwargs)`** calls `client.messages.create(**kwargs)` (don't pass `name` to the client) and appends one dict to `self.records`:

   ```python
   {"name": "greet", "model": "claude-opus-5-5", "input_tokens": 1000, "output_tokens": 500,
    "cost_usd": 0.014, "latency_ms": 250.0, "error": None}
   ```

   - `model` comes from `kwargs["model"]`; tokens from `response.usage`.
   - `latency_ms` is `(clock() after − clock() before) × 1000`, rounded to 3 decimals. Use `self.clock`, never `time` directly, so tests can control it.
   - If the call raises, still append a record (tokens 0, `cost_usd` `None`, latency measured) with `error` set to a string containing the exception's `status_code`, e.g. `"RateLimited (429)"`. Then **re-raise**.
   - Return the response unchanged.
3. **`total_cost`**: the sum of all `cost_usd` values (treat `None` as 0), rounded to 6 decimals.

Hint: `try` / `except` / `else` / `finally` fits this exactly.

Check is free and offline: the tests pass a fake client whose responses carry `usage`. Run with an API key set makes one real, cheap Haiku call.
