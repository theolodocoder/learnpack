# Cost of a request

Every response carries `response.usage.input_tokens` and `response.usage.output_tokens`. Turn them into dollars.

Write:

```python
PRICES: dict[str, tuple[float, float]]   # model -> (input $ per 1M tokens, output $ per 1M tokens)

def cost_usd(model: str, usage) -> float: ...
```

1. Fill in `PRICES` for the three current models:

   | Model | Input / 1M | Output / 1M |
   |---|---|---|
   | `claude-opus-5-5` | $4 | $20 |
   | `claude-sonnet-5-5` | $2 | $10 |
   | `claude-haiku-5-5` | $0.10 | $0.50 |

2. `cost_usd` returns `input_tokens · input_price / 1_000_000 + output_tokens · output_price / 1_000_000`. `usage` is any object with `.input_tokens` and `.output_tokens` attributes (the real `response.usage`, or a test stand-in).
3. For a model not in `PRICES`, raise `ValueError` with a message naming the model. Silently returning 0 would hide a bug in your cost reports.

## Example

```python
from types import SimpleNamespace
cost_usd("claude-opus-5-5", SimpleNamespace(input_tokens=2_000, output_tokens=500))
# 0.018   (2000 · 4 / 1M = 0.008, plus 500 · 20 / 1M = 0.010)
```
