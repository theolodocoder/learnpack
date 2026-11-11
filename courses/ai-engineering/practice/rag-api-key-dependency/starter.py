import os
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel


class Settings(BaseModel):
    api_key: str


def get_settings() -> Settings:
    # TODO: read APP_API_KEY from the environment (default "")
    raise NotImplementedError


def require_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    # TODO: raise HTTPException(401, "Invalid or missing API key") unless the key is configured
    #       and secrets.compare_digest(x_api_key, settings.api_key)
    pass


app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# TODO: GET /me, protected by require_api_key, returning {"authenticated": True}


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_settings] = lambda: Settings(api_key="s3cret")
    client = TestClient(app)
    print("no key:   ", client.get("/me").status_code)
    print("right key:", client.get("/me", headers={"X-API-Key": "s3cret"}).status_code)
