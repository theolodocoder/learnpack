from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def create_app(allowed_origins: list[str], max_body_bytes: int) -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        length = request.headers.get("content-length")
        if length is not None:
            if not length.isdigit():
                return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
            if int(length) > max_body_bytes:
                return JSONResponse({"detail": "Request body too large"}, status_code=413)
        return await call_next(request)

    # Added last so it runs first: even a 413 gets CORS headers the browser can read.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.post("/echo")
    async def echo(request: Request) -> dict:
        body = await request.body()
        return {"size": len(body)}

    return app


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(create_app(["https://myapp.com"], max_body_bytes=100))
    print(client.post("/echo", content=b"x" * 50).json())
    print(client.post("/echo", content=b"x" * 500).status_code)
    pre = client.options("/echo", headers={"Origin": "https://myapp.com", "Access-Control-Request-Method": "POST"})
    print(pre.status_code, pre.headers.get("access-control-allow-origin"))
