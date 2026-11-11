import time

# USD per 1M tokens: (input, output)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


class Tracer:
    def __init__(self, clock=time.perf_counter):
        self.clock = clock
        self.records: list[dict] = []

    def create(self, client, name: str, **kwargs):
        """Call client.messages.create(**kwargs) and record one trace entry."""
        record = {"name": name, "model": kwargs.get("model"), "input_tokens": 0, "output_tokens": 0,
                  "cost_usd": None, "latency_ms": 0.0, "error": None}
        start = self.clock()
        try:
            response = client.messages.create(**kwargs)
        except Exception as e:
            record["error"] = f"{type(e).__name__} ({getattr(e, 'status_code', None)})"
            raise
        else:
            record["input_tokens"] = response.usage.input_tokens
            record["output_tokens"] = response.usage.output_tokens
            record["cost_usd"] = cost_usd(record["model"], record["input_tokens"], record["output_tokens"])
            return response
        finally:
            record["latency_ms"] = round((self.clock() - start) * 1000, 3)
            self.records.append(record)

    def total_cost(self) -> float:
        return round(sum(r["cost_usd"] or 0.0 for r in self.records), 6)


if __name__ == "__main__":
    import anthropic

    tracer = Tracer()
    client = anthropic.Anthropic()
    tracer.create(client, "greet", model="claude-haiku-5-5", max_tokens=200,
                  messages=[{"role": "user", "content": "Say hi in five words."}])
    print(tracer.records, tracer.total_cost())
