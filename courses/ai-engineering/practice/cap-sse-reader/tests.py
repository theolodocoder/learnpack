import json

import httpx

from solution import stream_answer


def make_client(body: bytes, status: int = 200, seen: list | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, content=body, headers={"content-type": "text/event-stream"})
    return httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))


def sse(*events) -> bytes:
    return "".join(f"data: {e if isinstance(e, str) else json.dumps(e)}\n\n" for e in events).encode()


def test_yields_text_chunks_in_order():
    client = make_client(sse({"text": "Hello "}, {"text": "there"}, "[DONE]"))
    got = list(stream_answer(client, "Hi"))
    assert got == ["Hello ", "there"], f"expected ['Hello ', 'there'], got {got!r}"


def test_posts_the_question_as_json():
    seen = []
    list(stream_answer(make_client(sse("[DONE]"), seen=seen), "Do you deliver to Abuja?"))
    assert seen, "no request was sent"
    req = seen[0]
    assert req.method == "POST" and req.url.path == "/chat/stream", f"expected POST /chat/stream, got {req.method} {req.url.path}"
    body = json.loads(req.content)
    assert body == {"message": "Do you deliver to Abuja?"}, f"expected body {{'message': ...}}, got {body!r}"


def test_stops_at_done_and_ignores_other_lines():
    body = b': keep-alive comment\n\nevent: ping\n\n' + sse({"text": "a"}, "[DONE]", {"text": "after done"})
    got = list(stream_answer(make_client(body), "Hi"))
    assert got == ["a"], f"expected ['a'] (nothing after [DONE], comments ignored), got {got!r}"


def test_text_containing_newlines_survives():
    got = "".join(stream_answer(make_client(sse({"text": "line 1\nline 2"}, "[DONE]")), "Hi"))
    assert got == "line 1\nline 2", f"expected the newline to survive JSON decoding, got {got!r}"


def test_error_event_raises_runtime_error():
    gen = stream_answer(make_client(sse({"text": "Partial "}, {"error": "The AI service failed."}, "[DONE]")), "Hi")
    first = next(gen)
    assert first == "Partial ", f"expected the first chunk before the error, got {first!r}"
    try:
        next(gen)
    except RuntimeError as e:
        assert "The AI service failed." in str(e), f"the RuntimeError should carry the error message, got {e!r}"
    else:
        raise AssertionError("an error event should raise RuntimeError")


def test_http_error_status_raises():
    try:
        list(stream_answer(make_client(b'{"detail": "busy"}', status=503), "Hi"))
    except httpx.HTTPStatusError:
        return
    raise AssertionError("a 503 response should raise httpx.HTTPStatusError")
