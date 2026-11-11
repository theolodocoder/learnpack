import json
import logging
import sys

from fastapi.testclient import TestClient

from solution import JsonFormatter, create_app, request_id_var


def make_record(msg="hello %s", args=("world",), level=logging.INFO, extra=None, exc_info=None):
    record = logging.LogRecord("app.test", level, "x.py", 1, msg, args, exc_info)
    record.created = 0.0  # 1970-01-01, so the time is predictable
    for k, v in (extra or {}).items():
        setattr(record, k, v)
    return record


def formatted(record):
    out = JsonFormatter().format(record)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise AssertionError(f"format() must return one line of valid JSON, got {out!r}")


def test_formats_core_fields_as_json():
    data = formatted(make_record())
    want = {"time": "1970-01-01T00:00:00+00:00", "level": "INFO", "logger": "app.test",
            "message": "hello world", "request_id": "-"}
    got = {k: data.get(k) for k in want}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_includes_request_id_from_context_var():
    token = request_id_var.set("req-42")
    try:
        data = formatted(make_record())
    finally:
        request_id_var.reset(token)
    assert data["request_id"] == "req-42", f"expected 'req-42', got {data.get('request_id')!r}"


def test_includes_extra_fields():
    data = formatted(make_record(extra={"model": "claude-haiku-5-5", "tokens": 120}))
    assert data.get("model") == "claude-haiku-5-5" and data.get("tokens") == 120, \
        f"fields passed with extra= should appear in the JSON, got {data!r}"
    assert "args" not in data and "levelno" not in data, f"standard LogRecord attributes should not be dumped: {sorted(data)}"


def test_includes_exception_traceback():
    try:
        1 / 0
    except ZeroDivisionError:
        record = make_record(msg="boom", args=None, level=logging.ERROR, exc_info=sys.exc_info())
    data = formatted(record)
    assert "ZeroDivisionError" in data.get("exc_info", ""), f"expected a traceback in 'exc_info', got {data!r}"


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.setFormatter(JsonFormatter())

    def emit(self, record):
        self.lines.append(json.loads(self.format(record)))


def test_middleware_sets_and_echoes_request_id():
    handler = ListHandler()
    log = logging.getLogger("app")
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    try:
        client = TestClient(create_app())
        r = client.get("/ping", headers={"X-Request-ID": "abc123"})
        r2 = client.get("/ping")
    finally:
        log.removeHandler(handler)
    assert r.headers.get("x-request-id") == "abc123", f"incoming X-Request-ID should be echoed, got {r.headers.get('x-request-id')!r}"
    assert handler.lines and handler.lines[0]["request_id"] == "abc123", f"the log line should carry the request id, got {handler.lines!r}"
    new_id = r2.headers.get("x-request-id", "")
    assert len(new_id) >= 16 and new_id != "abc123", f"without a header, generate a fresh id, got {new_id!r}"
    assert handler.lines[1]["request_id"] == new_id, "the generated id should appear in the log line too"
    assert request_id_var.get() == "-", "reset the context var after the request"
