import httpx

from solution import get_json, get_user_or_none


def _client(handler, seen=None):
    def wrapped(request):
        if seen is not None:
            seen.append(request)
        return handler(request)

    return httpx.Client(base_url="https://api.example.com", transport=httpx.MockTransport(wrapped))


def test_get_json_returns_parsed_body():
    with _client(lambda r: httpx.Response(200, json={"ok": True})) as c:
        got = get_json(c, "/health")
    assert got == {"ok": True}, f"expected {{'ok': True}}, got {got!r}"


def test_get_json_sends_query_params():
    seen = []
    with _client(lambda r: httpx.Response(200, json=[]), seen) as c:
        get_json(c, "/search", params={"q": "llm", "limit": 2})
    req = seen[0]
    assert req.method == "GET" and req.url.path == "/search", f"expected GET /search, got {req.method} {req.url.path}"
    got = dict(req.url.params)
    assert got == {"q": "llm", "limit": "2"}, f"expected query q=llm&limit=2, got {got!r}"


def test_get_json_raises_on_server_error():
    with _client(lambda r: httpx.Response(500, json={"error": "down"})) as c:
        try:
            get_json(c, "/broken")
        except httpx.HTTPStatusError:
            return
    raise AssertionError("a 500 response should raise httpx.HTTPStatusError")


def test_get_user_or_none_returns_user():
    seen = []
    with _client(lambda r: httpx.Response(200, json={"id": 7, "name": "Grace"}), seen) as c:
        got = get_user_or_none(c, 7)
    assert seen[0].url.path == "/users/7", f"expected GET /users/7, got {seen[0].url.path}"
    assert got == {"id": 7, "name": "Grace"}, f"got {got!r}"


def test_get_user_or_none_returns_none_on_404():
    with _client(lambda r: httpx.Response(404, json={"error": "not found"})) as c:
        got = get_user_or_none(c, 999)
    assert got is None, f"expected None for a 404, got {got!r}"


def test_get_user_or_none_does_not_hide_other_errors():
    with _client(lambda r: httpx.Response(503, text="unavailable")) as c:
        try:
            get_user_or_none(c, 1)
        except httpx.HTTPStatusError as err:
            assert err.response.status_code == 503
            return
    raise AssertionError("a 503 should propagate, not turn into None")
