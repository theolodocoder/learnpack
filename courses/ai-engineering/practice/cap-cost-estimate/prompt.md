# Estimate LLM cost per month

Every capstone architecture needs a cost line: "at 50 users this costs about $X a month". Write the estimator, then use it to pick a model that fits a budget.

## 1. `estimate_monthly_cost`

```python
def estimate_monthly_cost(users: int, msgs_per_user: int, in_tokens: int, out_tokens: int,
                          prices: dict[str, float]) -> float:
```

- `msgs_per_user` is messages per user **per month**; `in_tokens` and `out_tokens` are the average tokens per message (input includes the system prompt, history and any retrieved context).
- `prices` is `{"input": dollars_per_million, "output": dollars_per_million}`.
- Return the monthly cost in dollars, **rounded to 2 decimal places**:

```
messages = users · msgs_per_user
cost = messages · (in_tokens · prices["input"] + out_tokens · prices["output"]) / 1_000_000
```

- If any of the four counts is negative, raise `ValueError`.

## 2. `pick_model`

```python
def pick_model(budget: float, users: int, msgs_per_user: int, in_tokens: int, out_tokens: int,
               models: dict[str, dict[str, float]]) -> str | None:
```

`models` maps model names to price dicts, **listed best-first**. Return the name of the first model whose estimated monthly cost is `<= budget`, or `None` if none fits.

## Example

```python
OPUS = {"input": 4.0, "output": 20.0}
HAIKU = {"input": 0.10, "output": 0.50}
estimate_monthly_cost(50, 200, 3000, 400, OPUS)    # 200.0
estimate_monthly_cost(50, 200, 3000, 400, HAIKU)   # 5.0
MODELS = {"claude-opus-5-5": OPUS, "claude-sonnet-5-5": {"input": 2.0, "output": 10.0}, "claude-haiku-5-5": HAIKU}
pick_model(150, 50, 200, 3000, 400, MODELS)        # 'claude-sonnet-5-5'  (costs $100)
pick_model(1, 50, 200, 3000, 400, MODELS)          # None
```
