from fake_llm import FakeAnthropic, reply, text
from solution import stream_text


def test_calling_it_does_not_hit_the_api_yet():
    client = FakeAnthropic([reply(text("One, two, three."))])
    stream_text(client, "Count to three")
    assert len(client.calls) == 0, "stream_text(...) made an API call before anyone iterated it; it should be a generator (use yield)"


def test_yields_chunks_in_order():
    client = FakeAnthropic([reply(text("One, two, three."))])
    got = list(stream_text(client, "Count to three"))
    want = ["One, ", "two, ", "three."]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_first_chunk_arrives_before_the_rest():
    client = FakeAnthropic([reply(text("alpha beta gamma"))])
    gen = stream_text(client, "x")
    first = next(gen)
    assert first == "alpha ", f"expected the first chunk 'alpha ', got {first!r}"


def test_sends_system_only_when_given():
    client = FakeAnthropic([reply(text("a")), reply(text("b"))])
    list(stream_text(client, "hi"))
    list(stream_text(client, "hi", system="Be brief."))
    assert "system" not in client.calls[0], f"don't send system when it's empty; sent {client.calls[0].get('system')!r}"
    assert client.calls[1].get("system") == "Be brief.", f"expected system 'Be brief.', got {client.calls[1].get('system')!r}"


def test_sends_model_and_prompt():
    client = FakeAnthropic([reply(text("ok"))])
    list(stream_text(client, "Hello", model="claude-sonnet-5-5"))
    sent = client.calls[0]
    assert sent.get("model") == "claude-sonnet-5-5", f"expected model 'claude-sonnet-5-5', got {sent.get('model')!r}"
    assert sent.get("messages") == [{"role": "user", "content": "Hello"}], f"unexpected messages: {sent.get('messages')!r}"
