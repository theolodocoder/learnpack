import json

from fastapi.testclient import TestClient

from fake_llm import FakeAnthropic, Overloaded, reply, text
from solution import app, get_client, sse_event


class _AsyncStream:
    def __init__(self, sync_stream):
        self.s = sync_stream

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    async def text_stream(self):
        for chunk in self.s.text_stream:
            yield chunk


class AsyncFake:
    """Wraps the sync FakeAnthropic so `async with client.messages.stream(...)` works."""
    def __init__(self, fake):
        self.fake = fake
        self.messages = self

    def stream(self, **kwargs):
        return _AsyncStream(self.fake.messages.stream(**kwargs))


def post(script, message="Hi"):
    fake = FakeAnthropic(script)
    app.dependency_overrides[get_client] = lambda: AsyncFake(fake)
    try:
        return TestClient(app).post("/chat/stream", json={"message": message}), fake
    finally:
        app.dependency_overrides.clear()


def events(body: str) -> list[str]:
    return [block.removeprefix("data: ") for block in body.split("\n\n") if block]


def test_sse_event_format():
    got = sse_event({"text": "line one\nline two"})
    want = 'data: {"text": "line one\\nline two"}\n\n'
    assert got == want, f"expected {want!r}, got {got!r}"


def test_streams_text_chunks_then_done():
    r, _ = post([reply(text("Hello there friend"))])
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
    evs = events(r.text)
    assert evs and evs[-1] == "[DONE]", f"the stream must end with 'data: [DONE]', got {evs!r}"
    chunks = [json.loads(e)["text"] for e in evs[:-1]]
    assert chunks == ["Hello ", "there ", "friend"], f"expected one event per chunk, got {chunks!r}"
    assert r.text.endswith("\n\n"), "every event (including [DONE]) must end with a blank line"


def test_uses_event_stream_media_type():
    r, _ = post([reply(text("ok"))])
    ct = r.headers.get("content-type", "")
    assert ct.startswith("text/event-stream"), f"content-type should be text/event-stream, got {ct!r}"


def test_sends_the_message_to_claude():
    _, fake = post([reply(text("ok"))], message="Tell me a joke")
    sent = fake.calls[0]
    want = [{"role": "user", "content": "Tell me a joke"}]
    assert sent.get("messages") == want, f"expected messages {want!r}, got {sent.get('messages')!r}"
    assert sent.get("model") == "claude-opus-5-5" and sent.get("max_tokens") == 1024, \
        f"use model=MODEL and max_tokens=1024, got {sent.get('model')!r}, {sent.get('max_tokens')!r}"


def test_api_error_becomes_error_event():
    r, _ = post([Overloaded()])
    assert r.status_code == 200, "the stream has already started, so the status stays 200"
    evs = events(r.text)
    want = ['{"error": "The AI service failed. Please try again."}', "[DONE]"]
    assert evs == want, f"expected an error event then [DONE], got {evs!r}"
