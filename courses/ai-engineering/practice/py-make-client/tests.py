import httpx

from solution import make_client


def test_uses_default_base_url_and_bearer_header():
    with make_client({"WEATHER_API_KEY": "abc123"}) as c:
        assert str(c.base_url) == "https://api.weather.example", f"got base_url {c.base_url}"
        got = c.headers.get("authorization")
        assert got == "Bearer abc123", f"expected 'Bearer abc123', got {got!r}"


def test_uses_base_url_from_env():
    env = {"WEATHER_API_KEY": "k", "WEATHER_API_URL": "https://staging.weather.example"}
    with make_client(env) as c:
        assert str(c.base_url) == "https://staging.weather.example", f"got base_url {c.base_url}"


def test_sets_ten_second_timeout():
    with make_client({"WEATHER_API_KEY": "k"}) as c:
        assert c.timeout.read == 10.0 and c.timeout.connect == 10.0, f"expected a 10 s timeout, got {c.timeout!r}"


def test_requests_carry_the_key_through_the_transport():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={})

    with make_client({"WEATHER_API_KEY": "secret"}, transport=httpx.MockTransport(handler)) as c:
        c.get("/today")
    assert seen, "the request didn't go through the transport you were given"
    req = seen[0]
    assert str(req.url) == "https://api.weather.example/today", f"got URL {req.url}"
    assert req.headers.get("authorization") == "Bearer secret", f"got headers {dict(req.headers)!r}"


def test_missing_or_empty_key_raises_runtime_error():
    for env in ({}, {"WEATHER_API_KEY": ""}):
        try:
            make_client(env)
        except RuntimeError as e:
            assert "WEATHER_API_KEY" in str(e), f"the error should name WEATHER_API_KEY, got {e!r}"
        else:
            raise AssertionError(f"make_client({env!r}) should raise RuntimeError")
