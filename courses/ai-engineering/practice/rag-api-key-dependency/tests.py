import os

from fastapi.testclient import TestClient

from solution import Settings, app, get_settings

client = TestClient(app)


def use_key(key: str):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=key)


def test_get_settings_reads_environment():
    os.environ["APP_API_KEY"] = "from-env"
    try:
        got = get_settings().api_key
    finally:
        del os.environ["APP_API_KEY"]
    assert got == "from-env", f"get_settings() should read APP_API_KEY, got {got!r}"


def test_health_needs_no_key():
    use_key("s3cret")
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}, f"/health should be open, got {r.status_code} {r.text}"


def test_missing_or_wrong_key_is_401():
    use_key("s3cret")
    for headers in ({}, {"X-API-Key": "wrong"}, {"X-API-Key": ""}):
        r = client.get("/me", headers=headers)
        assert r.status_code == 401, f"headers {headers!r} should get 401, got {r.status_code}"
        assert r.json() == {"detail": "Invalid or missing API key"}, f"unexpected body {r.json()!r}"


def test_right_key_is_accepted():
    use_key("s3cret")
    r = client.get("/me", headers={"X-API-Key": "s3cret"})
    assert r.status_code == 200, f"the right key should get 200, got {r.status_code} {r.text}"
    assert r.json() == {"authenticated": True}, f"expected {{'authenticated': True}}, got {r.json()!r}"


def test_unconfigured_server_refuses_everyone():
    use_key("")
    for headers in ({}, {"X-API-Key": ""}, {"X-API-Key": "anything"}):
        r = client.get("/me", headers=headers)
        assert r.status_code == 401, f"with no key configured, {headers!r} must get 401, got {r.status_code}"
    app.dependency_overrides.clear()
