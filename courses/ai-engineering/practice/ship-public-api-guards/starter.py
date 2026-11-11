from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def create_app(allowed_origins: list[str], max_body_bytes: int) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        # TODO: read the Content-Length header (it may be missing: then let the request through)
        #   not all digits      -> 400 {"detail": "Invalid Content-Length"}
        #   > max_body_bytes    -> 413 {"detail": "Request body too large"}
        return await call_next(request)

    # TODO: add CORSMiddleware allowing only `allowed_origins`,
    #       methods GET and POST, and headers Content-Type and X-API-Key

    @app.post("/echo")
    async def echo(request: Request) -> dict:
        body = await request.body()
        return {"size": len(body)}

    return app


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(create_app(["https://myapp.com"], max_body_bytes=100))
    print("small:", client.post("/echo", content=b"x" * 50).status_code)
    print("large:", client.post("/echo", content=b"x" * 500).status_code, "(want 413)")
    pre = client.options("/echo", headers={"Origin": "https://myapp.com", "Access-Control-Request-Method": "POST"})
    print("preflight:", pre.status_code, pre.headers.get("access-control-allow-origin"))
