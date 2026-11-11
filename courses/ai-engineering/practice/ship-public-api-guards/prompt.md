# Guards for a public API: CORS and a body size limit

Once your API has a public URL, two things change: browsers on other sites will try to call it, and anyone can send it a 500 MB request. Write

```python
def create_app(allowed_origins: list[str], max_body_bytes: int) -> FastAPI: ...
```

that returns an app with a `POST /echo` route (given in the starter) and two guards:

1. **Body size limit** as an HTTP middleware (`@app.middleware("http")`) that checks the `Content-Length` header before the body is read:
   - missing header → let the request through
   - not a whole number (e.g. `"abc"`) → `400 {"detail": "Invalid Content-Length"}`
   - larger than `max_body_bytes` → `413 {"detail": "Request body too large"}`
   - otherwise → `await call_next(request)`
2. **CORS** with FastAPI's `CORSMiddleware`: only `allowed_origins` may call the API from a browser, with methods `GET` and `POST` and headers `Content-Type` and `X-API-Key`. Never `["*"]` for an API that takes an API key.

## Example

```python
client = TestClient(create_app(["https://myapp.com"], max_body_bytes=100))
client.post("/echo", content=b"x" * 100).json()     # {'size': 100}
client.post("/echo", content=b"x" * 101).status_code # 413
r = client.options("/echo", headers={"Origin": "https://myapp.com",
                                     "Access-Control-Request-Method": "POST"})
r.headers["access-control-allow-origin"]             # 'https://myapp.com'
```

A preflight from `https://evil.example` must get no `access-control-allow-origin` header.

> **Note:** A client can send a body without `Content-Length` (chunked encoding). The middleware lets those through; in production, your reverse proxy or platform usually enforces a hard limit too.
