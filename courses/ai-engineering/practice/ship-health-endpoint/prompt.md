# Health and readiness endpoints

Hosting platforms and load balancers poll a URL to decide whether your app is up. Write two endpoints:

- **`GET /health`** (liveness): is the process running? It must be cheap and must **not** touch the database. It always returns `200 {"status": "ok", "version": <version>}`.
- **`GET /ready`** (readiness): can the app serve real requests right now? It calls `check_db()`:
  - returns `True` → `200 {"status": "ok", "checks": {"database": "ok"}}`
  - returns `False` **or raises** → `503 {"status": "unavailable", "checks": {"database": "error"}}`

```python
def create_app(check_db: Callable[[], bool], version: str = "dev") -> FastAPI: ...
```

`check_db` is passed in so tests can use a fake. In your real app it would run `SELECT 1` against Postgres. To return a status other than 200 with a body, return `JSONResponse(content, status_code=503)`.

## Example

```python
client = TestClient(create_app(check_db=lambda: False, version="1.2.0"))
client.get("/health").json()      # {'status': 'ok', 'version': '1.2.0'}
r = client.get("/ready")
r.status_code, r.json()           # (503, {'status': 'unavailable', 'checks': {'database': 'error'}})
```

A check that raises (say, `ConnectionError`) must give 503, not a 500 crash.
