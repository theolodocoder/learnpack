from fastapi.testclient import TestClient

from solution import create_app

ORIGIN = "https://myapp.com"
client = TestClient(create_app([ORIGIN], max_body_bytes=100))


def preflight(origin):
    return client.options("/echo", headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                                            "Access-Control-Request-Headers": "content-type,x-api-key"})


def test_small_body_reaches_the_handler():
    r = client.post("/echo", content=b"x" * 100)
    assert r.status_code == 200, f"a 100-byte body is allowed, got {r.status_code}"
    assert r.json() == {"size": 100}, f"got {r.json()!r}"


def test_large_body_is_rejected_with_413():
    r = client.post("/echo", content=b"x" * 101)
    assert r.status_code == 413, f"a 101-byte body should get 413, got {r.status_code}"
    assert r.json() == {"detail": "Request body too large"}, f"got {r.json()!r}"


def test_non_numeric_content_length_is_400():
    r = client.post("/echo", content=b"hi", headers={"Content-Length": "abc"})
    assert r.status_code == 400, f"Content-Length 'abc' should get 400, got {r.status_code}"


def test_preflight_from_allowed_origin_is_accepted():
    r = preflight(ORIGIN)
    assert r.status_code == 200, f"preflight from an allowed origin should be 200, got {r.status_code}"
    got = r.headers.get("access-control-allow-origin")
    assert got == ORIGIN, f"expected Access-Control-Allow-Origin {ORIGIN!r}, got {got!r}"
    allowed = r.headers.get("access-control-allow-headers", "").lower()
    assert "x-api-key" in allowed, f"X-API-Key should be an allowed header, got {allowed!r}"


def test_other_origins_get_no_cors_permission():
    r = preflight("https://evil.example")
    assert r.headers.get("access-control-allow-origin") is None, "an unknown origin must not get Access-Control-Allow-Origin"
    r = client.post("/echo", content=b"x", headers={"Origin": "https://evil.example"})
    assert r.headers.get("access-control-allow-origin") is None, "simple requests from unknown origins must not be allowed"
