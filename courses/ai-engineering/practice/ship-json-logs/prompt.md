# JSON logs with a request id

Write a `logging.Formatter` that prints each log record as one line of JSON, and a FastAPI middleware that gives every request an id that appears in every log line written while handling it.

```python
request_id_var: ContextVar[str]   # given, default "-"

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str: ...

def create_app() -> FastAPI: ...   # GET /ping is given; add the middleware
```

**`JsonFormatter.format`** returns `json.dumps(...)` of a dict with:

- `time`: `record.created` as ISO 8601 in UTC: `datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()`
- `level` (`record.levelname`), `logger` (`record.name`), `message` (`record.getMessage()`, which fills in `%s` args)
- `request_id`: `request_id_var.get()`
- every attribute added with `extra=` (anything in `vars(record)` that isn't in the given `_STANDARD` set)
- `exc_info`: `self.formatException(record.exc_info)`, only when `record.exc_info` is set

Use `default=str` in `json.dumps` so odd values don't crash logging.

**The middleware** reads the `X-Request-ID` header (or makes `uuid.uuid4().hex`), sets `request_id_var` for the request, resets it in a `finally` using the token `set()` returned, and adds `X-Request-ID` to the response.

## Example

```python
record = logging.LogRecord("app", logging.INFO, "x.py", 1, "hello %s", ("world",), None)
record.created = 0.0
record.tokens = 120
JsonFormatter().format(record)
# '{"time": "1970-01-01T00:00:00+00:00", "level": "INFO", "logger": "app",
#   "message": "hello world", "request_id": "-", "tokens": 120}'
```
