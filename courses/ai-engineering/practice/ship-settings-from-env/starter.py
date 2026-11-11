from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError


class ConfigError(Exception):
    """Raised at startup when the environment is missing or has bad settings."""


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    # TODO: declare the five fields with their types, defaults and limits:
    #   anthropic_api_key: SecretStr, required, not empty
    #   database_url: str, required, not empty
    #   model: str = "claude-haiku-5-5"
    #   max_tokens: int = 1024, greater than 0 and at most 64000
    #   environment: "dev" or "prod", default "dev"
    pass


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build Settings from environment variables named after the fields in UPPER_CASE.

    Raise ConfigError naming every bad or missing variable.
    """
    # TODO: pick out the env vars that match a field (Settings.model_fields gives the names)
    # TODO: build Settings; on ValidationError raise ConfigError listing the UPPER_CASE names
    raise NotImplementedError


if __name__ == "__main__":
    try:
        good = {"ANTHROPIC_API_KEY": "sk-ant-demo", "DATABASE_URL": "postgresql://localhost/app", "MAX_TOKENS": "2048"}
        print(load_settings(good))
        load_settings({"MAX_TOKENS": "lots"})
    except ConfigError as e:
        print("ConfigError:", e)
    except NotImplementedError:
        print("load_settings isn't written yet: fill in the TODOs, then Run again.")
