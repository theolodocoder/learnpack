# Build a configured client from the environment

Real programs never hard-code API keys. They read them from environment variables (often loaded from a `.env` file) and build one client with the right base URL, headers and timeout.

```python
def make_client(env: Mapping[str, str], transport: httpx.BaseTransport | None = None) -> httpx.Client:
```

- Read the key from `env["WEATHER_API_KEY"]`. If it is missing or empty, raise `RuntimeError` with a message that names the variable.
- Read the base URL from `env["WEATHER_API_URL"]`, defaulting to `"https://api.weather.example"`.
- Return an `httpx.Client` with:
  - that `base_url`,
  - the header `Authorization: Bearer <key>`,
  - a 10-second timeout (`timeout=10.0`),
  - `transport=transport` (tests pass a `MockTransport`; `None` means the normal network).

`env` is a parameter (instead of reading `os.environ` inside) so tests can pass a plain dict. In real code you'd call `make_client(os.environ)` after `load_dotenv()`.

Example:

```python
client = make_client({"WEATHER_API_KEY": "abc123"})
client.base_url                    # URL('https://api.weather.example')
client.headers["authorization"]    # 'Bearer abc123'
```
