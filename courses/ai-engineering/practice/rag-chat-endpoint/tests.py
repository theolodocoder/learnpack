from fastapi.testclient import TestClient

from fake_llm import BadRequest, FakeAnthropic, Overloaded, RateLimited, reply, text
from solution import SYSTEM, app, get_client, llm_error_to_http


class AsyncFake:
    """Wraps the sync FakeAnthropic so `await client.messages.create(...)` works."""
    def __init__(self, fake):
        self.fake = fake
        self.messages = self

    async def create(self, **kwargs):
        return self.fake.messages.create(**kwargs)


def post(script, body):
    fake = FakeAnthropic(script)
    app.dependency_overrides[get_client] = lambda: AsyncFake(fake)
    try:
        return TestClient(app).post("/chat", json=body), fake
    finally:
        app.dependency_overrides.clear()


def test_returns_reply_and_usage():
    r, _ = post([reply(text("Hello "), text("there!"), input_tokens=12, output_tokens=3)], {"message": "Hi"})
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}"
    want = {"reply": "Hello there!", "input_tokens": 12, "output_tokens": 3}
    assert r.json() == want, f"expected {want!r}, got {r.json()!r}"


def test_sends_model_system_and_message():
    _, fake = post([reply(text("ok"))], {"message": "What are your hours?"})
    assert len(fake.calls) == 1, f"expected one API call, got {len(fake.calls)}"
    sent = fake.calls[0]
    assert sent.get("model") == "claude-opus-5-5", f"model should be MODEL, got {sent.get('model')!r}"
    assert sent.get("system") == SYSTEM, "pass system=SYSTEM"
    assert sent.get("max_tokens") == 1024, f"max_tokens should be 1024, got {sent.get('max_tokens')!r}"
    want = [{"role": "user", "content": "What are your hours?"}]
    assert sent.get("messages") == want, f"expected messages {want!r}, got {sent.get('messages')!r}"


def test_invalid_message_is_422_without_calling_claude():
    for body in ({"message": ""}, {"message": "x" * 4001}, {}):
        r, fake = post([reply(text("never"))], body)
        assert r.status_code == 422, f"{str(body)[:40]}... should be rejected with 422, got {r.status_code}"
        assert fake.calls == [], "invalid input must not reach the API (that costs money)"


def test_rate_limit_and_overload_become_503():
    for err in (RateLimited(), Overloaded()):
        r, _ = post([err], {"message": "Hi"})
        assert r.status_code == 503, f"{type(err).__name__} (status {err.status_code}) should map to 503, got {r.status_code}"
        assert r.json() == {"detail": "The AI service is busy. Please try again shortly."}, f"unexpected body {r.json()!r}"


def test_bad_request_becomes_502():
    r, _ = post([BadRequest()], {"message": "Hi"})
    assert r.status_code == 502, f"an upstream 400 should map to 502, got {r.status_code}"
    assert r.json() == {"detail": "The AI service rejected the request."}, f"unexpected body {r.json()!r}"


def test_mapping_function_directly():
    class E(Exception):
        def __init__(self, code):
            self.status_code = code

    got = {code: llm_error_to_http(E(code)).status_code for code in (429, 500, 529, 400, 401, 404)}
    want = {429: 503, 500: 503, 529: 503, 400: 502, 401: 502, 404: 502}
    assert got == want, f"expected {want!r}, got {got!r}"
