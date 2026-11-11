import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import FastAPI, Request

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# Attributes every LogRecord has; anything else came from `extra=`.
_STANDARD = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # TODO: build a dict with
        #   time (ISO 8601 UTC from record.created), level, logger, message (record.getMessage()),
        #   request_id (from request_id_var), every extra attribute not in _STANDARD,
        #   and exc_info (self.formatException(record.exc_info)) if there is one.
        # TODO: return json.dumps(data, default=str)
        return super().format(record)


logger = logging.getLogger("app")


def create_app() -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        # TODO: use the incoming X-Request-ID header, or uuid.uuid4().hex if there isn't one
        # TODO: set request_id_var for the request, and reset it afterwards (in a finally)
        # TODO: add the id to the response as the X-Request-ID header
        return await call_next(request)

    @app.get("/ping")
    def ping() -> dict:
        logger.info("ping received", extra={"user": "demo"})
        return {"pong": True}

    return app


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    r = client.get("/ping", headers={"X-Request-ID": "abc123"})
    print("response header:", r.headers.get("x-request-id"))
