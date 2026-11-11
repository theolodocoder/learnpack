from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError


class ConfigError(Exception):
    """Raised at startup when the environment is missing or has bad settings."""


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    anthropic_api_key: SecretStr = Field(min_length=1)
    database_url: str = Field(min_length=1)
    model: str = "claude-haiku-5-5"
    max_tokens: int = Field(default=1024, gt=0, le=64000)
    environment: Literal["dev", "prod"] = "dev"


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build Settings from environment variables (field name in UPPER_CASE). Fail fast."""
    values = {name: env[name.upper()] for name in Settings.model_fields if name.upper() in env}
    try:
        return Settings(**values)
    except ValidationError as e:
        bad = sorted({str(err["loc"][0]).upper() for err in e.errors()})
        raise ConfigError(f"Invalid or missing settings: {', '.join(bad)}") from e


if __name__ == "__main__":
    good = {"ANTHROPIC_API_KEY": "sk-ant-demo", "DATABASE_URL": "postgresql://localhost/app", "MAX_TOKENS": "2048"}
    print(load_settings(good))
    try:
        load_settings({"MAX_TOKENS": "lots"})
    except ConfigError as e:
        print("ConfigError:", e)
