import time

# USD per 1M tokens: (input, output)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    # TODO: None for an unknown model; otherwise the dollar cost rounded to 6 decimals
    return None


class Tracer:
    def __init__(self, clock=time.perf_counter):
        self.clock = clock
        self.records: list[dict] = []

    def create(self, client, name: str, **kwargs):
        """Call client.messages.create(**kwargs), append one record, return the response.

        Record keys: name, model, input_tokens, output_tokens, cost_usd, latency_ms, error.
        On an exception: record error (with the status_code), then re-raise.
        """
        # TODO: read the clock before and after the call (use try / except / finally)
        return client.messages.create(**kwargs)

    def total_cost(self) -> float:
        # TODO: sum of cost_usd over all records (None counts as 0), rounded to 6 decimals
        return 0.0


if __name__ == "__main__":
    import anthropic

    tracer = Tracer()
    try:
        client = anthropic.Anthropic()
        tracer.create(client, "greet", model="claude-haiku-5-5", max_tokens=200,
                      messages=[{"role": "user", "content": "Say hi in five words."}])
    except Exception as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", type(e).__name__)
    print(tracer.records, tracer.total_cost())
