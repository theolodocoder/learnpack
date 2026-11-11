from fastapi.testclient import TestClient

from solution import create_app


class CountingCheck:
    def __init__(self, result=True, error=None):
        self.result, self.error, self.calls = result, error, 0

    def __call__(self):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def test_health_returns_ok_and_version():
    r = TestClient(create_app(check_db=CountingCheck(), version="1.2.0")).get("/health")
    assert r.status_code == 200, f"expected 200, got {r.status_code}"
    assert r.json() == {"status": "ok", "version": "1.2.0"}, f"got {r.json()!r}"


def test_health_does_not_touch_the_database():
    check = CountingCheck(result=False)
    r = TestClient(create_app(check_db=check)).get("/health")
    assert r.status_code == 200, f"/health is a liveness check and should be 200 even if the DB is down, got {r.status_code}"
    assert check.calls == 0, f"/health should not call check_db, it was called {check.calls} time(s)"


def test_ready_is_200_when_database_is_up():
    check = CountingCheck(result=True)
    r = TestClient(create_app(check_db=check)).get("/ready")
    assert r.status_code == 200, f"expected 200, got {r.status_code}"
    assert r.json() == {"status": "ok", "checks": {"database": "ok"}}, f"got {r.json()!r}"
    assert check.calls == 1, f"/ready should call check_db once, got {check.calls}"


def test_ready_is_503_when_database_check_fails():
    r = TestClient(create_app(check_db=CountingCheck(result=False))).get("/ready")
    assert r.status_code == 503, f"expected 503, got {r.status_code}"
    assert r.json() == {"status": "unavailable", "checks": {"database": "error"}}, f"got {r.json()!r}"


def test_ready_is_503_not_500_when_check_raises():
    app = create_app(check_db=CountingCheck(error=ConnectionError("db down")))
    r = TestClient(app, raise_server_exceptions=False).get("/ready")
    assert r.status_code == 503, f"an exception in check_db should give 503, got {r.status_code}"
    assert r.json()["checks"] == {"database": "error"}, f"got {r.json()!r}"
