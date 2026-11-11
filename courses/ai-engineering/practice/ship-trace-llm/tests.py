from fake_llm import FakeAnthropic, RateLimited, reply, text

from solution import Tracer, cost_usd


class FakeClock:
    """Returns the given times in order, one per call."""
    def __init__(self, *times):
        self.times = list(times)

    def __call__(self):
        return self.times.pop(0)


def test_cost_usd_uses_per_million_prices():
    cases = [(("claude-opus-5-5", 1000, 500), 0.014), (("claude-haiku-5-5", 1_000_000, 1_000_000), 0.6),
             (("claude-sonnet-5-5", 0, 0), 0.0), (("some-other-model", 10, 10), None)]
    for args, want in cases:
        got = cost_usd(*args)
        assert got == want, f"cost_usd{args} expected {want!r}, got {got!r}"


def test_records_model_tokens_cost_and_latency():
    fake = FakeAnthropic([reply(text("Hi!"), input_tokens=1000, output_tokens=500)])
    tracer = Tracer(clock=FakeClock(10.0, 10.25))
    resp = tracer.create(fake, "greet", model="claude-opus-5-5", max_tokens=100,
                         messages=[{"role": "user", "content": "Hi"}])
    assert resp.content[0].text == "Hi!", "create() must return the model's response unchanged"
    want = {"name": "greet", "model": "claude-opus-5-5", "input_tokens": 1000, "output_tokens": 500,
            "cost_usd": 0.014, "latency_ms": 250.0, "error": None}
    assert tracer.records == [want], f"expected [{want!r}], got {tracer.records!r}"


def test_passes_kwargs_through_to_the_client():
    fake = FakeAnthropic([reply(text("ok"))])
    tracer = Tracer(clock=FakeClock(0.0, 0.1))
    msgs = [{"role": "user", "content": "Q"}]
    tracer.create(fake, "q", model="claude-haiku-5-5", max_tokens=50, system="Be brief.", messages=msgs)
    sent = fake.calls[0]
    assert sent == {"model": "claude-haiku-5-5", "max_tokens": 50, "system": "Be brief.", "messages": msgs}, \
        f"the client should receive exactly the kwargs given (not 'name'), got {sent!r}"


def test_records_errors_and_reraises():
    fake = FakeAnthropic([RateLimited()])
    tracer = Tracer(clock=FakeClock(5.0, 5.5))
    try:
        tracer.create(fake, "busy", model="claude-haiku-5-5", max_tokens=10, messages=[])
    except RateLimited:
        pass
    else:
        raise AssertionError("the error should be re-raised after recording it")
    assert len(tracer.records) == 1, f"a failed call should still be recorded, got {tracer.records!r}"
    rec = tracer.records[0]
    assert rec["error"] and "429" in rec["error"], f"error should mention the status code 429, got {rec['error']!r}"
    assert rec["latency_ms"] == 500.0, f"latency is recorded for failures too, got {rec['latency_ms']!r}"
    assert rec["cost_usd"] is None, f"a failed call has no cost, got {rec['cost_usd']!r}"


def test_total_cost_sums_all_calls():
    fake = FakeAnthropic([reply(text("a"), input_tokens=2000, output_tokens=1000),
                          reply(text("b"), input_tokens=1000, output_tokens=0)])
    tracer = Tracer(clock=FakeClock(0, 1, 2, 3))
    for _ in range(2):
        tracer.create(fake, "x", model="claude-haiku-5-5", max_tokens=10, messages=[])
    got = tracer.total_cost()
    assert got == 0.0008, f"expected 0.0008 (0.0007 + 0.0001), got {got!r}"
