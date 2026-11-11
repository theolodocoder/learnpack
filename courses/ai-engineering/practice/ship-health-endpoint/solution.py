from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def create_app(check_db: Callable[[], bool], version: str = "dev") -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict:
        # Liveness: is the process up? Cheap, touches nothing else.
        return {"status": "ok", "version": version}

    @app.get("/ready")
    def ready() -> JSONResponse:
        # Readiness: can we actually serve requests? Check dependencies.
        try:
            db_ok = bool(check_db())
        except Exception:
            db_ok = False
        if db_ok:
            return JSONResponse({"status": "ok", "checks": {"database": "ok"}})
        return JSONResponse({"status": "unavailable", "checks": {"database": "error"}}, status_code=503)

    return app


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(create_app(check_db=lambda: True, version="1.2.0"))
    print(client.get("/health").json())
    print(client.get("/ready").status_code, client.get("/ready").json())
    broken = TestClient(create_app(check_db=lambda: False))
    print(broken.get("/ready").status_code, broken.get("/ready").json())
