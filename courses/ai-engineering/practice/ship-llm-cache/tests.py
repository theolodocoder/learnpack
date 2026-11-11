from fake_llm import FakeAnthropic, RateLimited, reply, text

from solution import TTLCache, cache_key, cached_answer


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def ask(client, cache, question="What is RAG?", model="claude-haiku-5-5"):
    return cached_answer(client, cache, model=model, system="Be brief.", question=question)


def test_cache_key_is_stable_and_sensitive():
    m1 = [{"role": "user", "content": "Hi"}]
    m2 = [{"content": "Hi", "role": "user"}]  # same message, different key order
    k = cache_key("claude-haiku-5-5", "sys", m1)
    assert len(k) == 64 and all(c in "0123456789abcdef" for c in k), f"expected a SHA-256 hex digest, got {k!r}"
    assert k == cache_key("claude-haiku-5-5", "sys", m2), "dict key order must not change the cache key"
    for other in (cache_key("claude-opus-5-5", "sys", m1), cache_key("claude-haiku-5-5", "other", m1),
                  cache_key("claude-haiku-5-5", "sys", [{"role": "user", "content": "Hi!"}])):
        assert other != k, "a different model, system prompt or message must give a different key"


def test_ttl_cache_expires_entries():
    clock = Clock()
    c = TTLCache(ttl_seconds=60, clock=clock)
    c.set("a", "x")
    clock.now = 59.9
    assert c.get("a") == "x", "an entry is still valid before the TTL"
    clock.now = 60.0
    assert c.get("a") is None, "an entry expires once the TTL has passed"
    assert c.get("missing") is None, "a missing key returns None"


def test_repeated_question_calls_the_model_once():
    fake = FakeAnthropic([reply(text("Retrieval-augmented generation."))])
    cache = TTLCache(60, clock=Clock())
    first, second = ask(fake, cache), ask(fake, cache)
    assert first == second == "Retrieval-augmented generation.", f"got {first!r} and {second!r}"
    assert len(fake.calls) == 1, f"the second identical question should be a cache hit, but the model was called {len(fake.calls)} times"
    sent = fake.calls[0]
    assert sent["system"] == "Be brief." and sent["messages"] == [{"role": "user", "content": "What is RAG?"}], f"unexpected call {sent!r}"


def test_different_question_or_model_misses():
    fake = FakeAnthropic([reply(text("a")), reply(text("b")), reply(text("c"))])
    cache = TTLCache(60, clock=Clock())
    got = [ask(fake, cache), ask(fake, cache, question="What is an agent?"), ask(fake, cache, model="claude-opus-5-5")]
    assert got == ["a", "b", "c"], f"each different request should call the model, got {got!r}"


def test_expired_entry_calls_again_and_errors_are_not_cached():
    clock = Clock()
    fake = FakeAnthropic([reply(text("old")), RateLimited(), reply(text("new"))])
    cache = TTLCache(60, clock=clock)
    assert ask(fake, cache) == "old"
    clock.now = 61
    try:
        ask(fake, cache)
        raise AssertionError("the RateLimited error should propagate")
    except RateLimited:
        pass
    got = ask(fake, cache)
    assert got == "new", f"after an error, the next call should hit the model again, got {got!r}"
    assert len(fake.calls) == 3, f"expected 3 model calls, got {len(fake.calls)}"
