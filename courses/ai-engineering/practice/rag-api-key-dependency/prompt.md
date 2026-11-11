# Protect an endpoint with an API key dependency

Your backend will call a paid API, so not just anyone should be able to use it. Write a dependency that checks an `X-API-Key` header, and make the settings it reads overridable in tests.

```python
class Settings(BaseModel):
    api_key: str

def get_settings() -> Settings: ...
def require_api_key(x_api_key: Annotated[str | None, Header()] = None,
                    settings: Settings = Depends(get_settings)) -> None: ...
```

1. **`get_settings()`** returns `Settings(api_key=os.environ.get("APP_API_KEY", ""))`.
2. **`require_api_key`** raises `HTTPException(401, detail="Invalid or missing API key")` when:
   - the header is missing, or
   - it doesn't match `settings.api_key`, or
   - `settings.api_key` is empty (a server with no key configured must refuse everyone, not accept everyone).

   Compare with `secrets.compare_digest`.
3. **`GET /health`** needs no key and returns `{"status": "ok"}`.
4. **`GET /me`** requires the key (use `dependencies=[Depends(require_api_key)]`) and returns `{"authenticated": True}`.

## Example

```python
app.dependency_overrides[get_settings] = lambda: Settings(api_key="s3cret")
client.get("/me").status_code                                  # 401
client.get("/me", headers={"X-API-Key": "s3cret"}).json()      # {"authenticated": True}
client.get("/health").json()                                   # {"status": "ok"}
```

The tests replace `get_settings` with `app.dependency_overrides`, so `require_api_key` must get its settings through `Depends(get_settings)`, not by calling `os.environ` itself.
