# Fail-fast settings from the environment

A deployed app reads its configuration from environment variables. If one is missing or wrong, it should refuse to start, with a message that says exactly which variable to fix. It shouldn't crash on the first request an hour later.

Write a Pydantic `Settings` model and a loader that takes the environment as a plain dict, so it's easy to test:

```python
class ConfigError(Exception): ...

class Settings(BaseModel):
    anthropic_api_key: SecretStr          # required, not empty
    database_url: str                     # required, not empty
    model: str = "claude-haiku-5-5"
    max_tokens: int = 1024                # > 0 and <= 64000
    environment: Literal["dev", "prod"] = "dev"

def load_settings(env: Mapping[str, str]) -> Settings: ...
```

Rules:

1. Each field is read from the environment variable with the same name in UPPER_CASE (`max_tokens` ← `MAX_TOKENS`). Other variables (`PATH`, `HOME`, …) are ignored.
2. Pydantic converts the strings: `"2048"` becomes `2048`.
3. If validation fails, raise `ConfigError` whose message names **every** bad or missing variable in UPPER_CASE, for example `Invalid or missing settings: ANTHROPIC_API_KEY, DATABASE_URL`.
4. The API key is a `SecretStr`, so printing the settings never shows it.

Hints: `Field(min_length=1)`, `Field(default=1024, gt=0, le=64000)`, `Settings.model_fields` (a dict of field names), and `ValidationError.errors()`, where each error's `"loc"` is a tuple whose first item is the field name.

## Example

```python
s = load_settings({"ANTHROPIC_API_KEY": "sk-ant-1", "DATABASE_URL": "postgresql://db/app", "MAX_TOKENS": "2048"})
s.max_tokens                         # 2048
s.model                              # 'claude-haiku-5-5'
s.anthropic_api_key                  # SecretStr('**********')
load_settings({"MAX_TOKENS": "lots"})
# ConfigError: Invalid or missing settings: ANTHROPIC_API_KEY, DATABASE_URL, MAX_TOKENS
```
