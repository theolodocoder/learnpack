from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def create_app(check_db: Callable[[], bool], version: str = "dev") -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict:
        # TODO: liveness. Return {"status": "ok", "version": version}. Don't call check_db.
        ...

    @app.get("/ready")
    def ready() -> JSONResponse:
        # TODO: readiness. Call check_db(); treat an exception as a failure.
        #   ok   -> 200 {"status": "ok", "checks": {"database": "ok"}}
        #   fail -> 503 {"status": "unavailable", "checks": {"database": "error"}}
        ...

    return app


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(create_app(check_db=lambda: True, version="1.2.0"), raise_server_exceptions=False)
    print("/health", client.get("/health").status_code, client.get("/health").text)
    print("/ready ", client.get("/ready").status_code, client.get("/ready").text)
