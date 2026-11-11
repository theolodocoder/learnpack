import os
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel


class Settings(BaseModel):
    api_key: str


def get_settings() -> Settings:
    return Settings(api_key=os.environ.get("APP_API_KEY", ""))


def require_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_key or x_api_key is None or not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/me", dependencies=[Depends(require_api_key)])
def me() -> dict:
    return {"authenticated": True}


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_settings] = lambda: Settings(api_key="s3cret")
    client = TestClient(app)
    print("no key:   ", client.get("/me").status_code)
    print("right key:", client.get("/me", headers={"X-API-Key": "s3cret"}).status_code)
