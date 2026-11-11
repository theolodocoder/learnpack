# Config, secrets and health checks

## Why this matters

The same code will soon run in three places: your laptop, a CI runner on GitHub, and a server on Railway or Render. Each needs different settings (database URL, model name, API keys) and none of those can be baked into the code. A leaked `ANTHROPIC_API_KEY` in a public repo gets found by bots within minutes, and a missing setting found in production at 2am is a bad way to learn it was required. This lesson sets up the configuration layer every later step relies on.

## 1. Configuration lives in the environment

The *Twelve-Factor App* is a short, widely used set of rules for building deployable web services. Its third rule is the one that matters here: **store config in the environment.** Config is everything that differs between deploys:

- credentials: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `APP_API_KEY`
- addresses of backing services: `DATABASE_URL`, `REDIS_URL`
- per-deploy knobs: `MODEL`, `LOG_LEVEL`, `ENVIRONMENT`

Code is everything that stays the same. The test from the twelve-factor site: could you open-source the repo right now without leaking a credential? If not, config is in your code.

Environment variables are strings a process inherits from whatever started it: your shell, Docker, GitHub Actions, or a hosting platform. Every one of those has a way to set them, which is why they're the universal interface.

```python
import os

os.environ["MODEL"]              # KeyError if missing
os.environ.get("MODEL")          # None if missing
os.environ.get("MODEL", "claude-haiku-5-5")  # default if missing
```

Two properties to remember: values are **always strings** (`"2048"`, not `2048`; `"false"` is a non-empty string, so it's truthy), and a missing variable is silent until you read it.

## 2. A validated `Settings` model, loaded at startup

Scattering `os.environ.get(...)` across files gives you both problems at once: unconverted strings, and missing values discovered only when that line runs. Put all config in one Pydantic model and build it once, when the app starts.

```python
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError


class ConfigError(Exception):
    pass


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)          # settings don't change while running

    anthropic_api_key: SecretStr = Field(min_length=1)
    database_url: str = Field(min_length=1)
    app_api_key: SecretStr = Field(min_length=1)
    model: str = "claude-haiku-5-5"
    max_tokens: int = Field(default=1024, gt=0, le=64000)
    environment: Literal["dev", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


def load_settings(env: Mapping[str, str]) -> Settings:
    values = {name: env[name.upper()] for name in Settings.model_fields if name.upper() in env}
    try:
        return Settings(**values)
    except ValidationError as e:
        bad = sorted({str(err["loc"][0]).upper() for err in e.errors()})
        raise ConfigError(f"Invalid or missing settings: {', '.join(bad)}") from e
```

What each piece buys you:

- **Types convert and validate.** `MAX_TOKENS="2048"` becomes `2048`; `MAX_TOKENS="lots"` fails. `Literal["dev", "prod"]` rejects a typo like `prdo`.
- **Required fields have no default.** If `DATABASE_URL` isn't set, `Settings(...)` fails.
- **`SecretStr`** hides the value when printed or logged, so a stray `print(settings)` or an error report won't leak the key. You get the real value with `.get_secret_value()` at the one place that needs it.
- **`load_settings` takes a mapping**, not `os.environ` directly. In the app you pass `os.environ`; in tests you pass a plain dict. No monkey-patching.

```python
s = load_settings({"ANTHROPIC_API_KEY": "sk-ant-1", "DATABASE_URL": "postgresql://db/app",
                   "APP_API_KEY": "k", "MAX_TOKENS": "2048"})
print(s.max_tokens, s.model)    # 2048 claude-haiku-5-5
print(s.anthropic_api_key)      # **********
load_settings({})
# ConfigError: Invalid or missing settings: ANTHROPIC_API_KEY, APP_API_KEY, DATABASE_URL
```

### Fail fast

Load settings **when the process starts**, not lazily on the first request. In FastAPI, the lifespan function runs before the server accepts traffic:

```python
import os
from contextlib import asynccontextmanager

import anthropic
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings(os.environ)          # raises ConfigError -> the app never starts
    app.state.settings = settings
    app.state.client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key.get_secret_value(), timeout=60.0)
    yield


app = FastAPI(lifespan=lifespan)
```

If a variable is missing, the deploy fails with a clear `ConfigError` in the logs, and the platform keeps the previous version serving traffic. That's much better than a deploy that "succeeds" and returns 500s.

> **Note:** The `pydantic-settings` package does this mapping for you: subclass `BaseSettings` and fields are filled from environment variables by name, including `.env` files. The FastAPI docs page *Settings and Environment Variables* shows it. The hand-written `load_settings` above is the same idea and needs no extra dependency.

> **Try it:** In the *Fail-fast settings* exercise, Run the starter after filling in the model, then delete `DATABASE_URL` from the dict and read the error message.

## 3. `.env` files: for your laptop only

Typing `export ANTHROPIC_API_KEY=...` in every terminal gets old. A `.env` file at the project root holds local values, and `python-dotenv` loads it into `os.environ`:

```
# .env  (never committed)
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://app:devpassword@localhost:5432/docs
APP_API_KEY=dev-key-change-me
MODEL=claude-haiku-5-5
```

```python
from dotenv import load_dotenv

load_dotenv()                     # does nothing if there's no .env; never overrides real env vars
settings = load_settings(os.environ)
```

`load_dotenv()` does **not** override variables that are already set, so on a server (which has no `.env`) the platform's values win. That's exactly the behaviour you want.

Commit a **`.env.example`** with every variable name and safe placeholder values. It documents what the app needs:

```
# .env.example  (committed)
ANTHROPIC_API_KEY=
DATABASE_URL=postgresql://app:devpassword@localhost:5432/docs
APP_API_KEY=
MODEL=claude-haiku-5-5
```

### `.gitignore` first, then `.env`

Create `.gitignore` **before** you create `.env`, and before your first commit:

```
# .gitignore
.env
.env.*
!.env.example
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

`!.env.example` re-includes the example after `.env.*` excluded it. Check it worked:

```bash
git check-ignore -v .env        # prints the .gitignore line that ignores it
git status                      # .env must not appear
```

> **Note:** `.gitignore` only affects files git isn't tracking yet. If `.env` was committed once, adding it to `.gitignore` doesn't remove it. Run `git rm --cached .env`, commit, **and treat the key as leaked** (next section).

## 4. When a key leaks

Assume a key is compromised the moment it's pushed to any remote, even a private repo, even if you delete the commit a minute later. Git history, forks, CI logs and caches all keep copies. GitHub runs **secret scanning** on public repos and recognises Anthropic API keys among hundreds of other formats, so a pushed key may be reported and revoked for you. Don't rely on that.

The order of operations:

1. **Revoke first.** In the Claude Console, open API keys and delete (or disable) the leaked key. Until you do this, nothing else matters.
2. **Create a new key** and put it where it's needed: your local `.env`, the hosting platform's variables, GitHub Actions secrets.
3. **Redeploy** so the running app picks up the new value. Environment variables are read at startup.
4. **Check usage** in the Console for calls you didn't make.
5. **Clean up the repo:** remove the file from tracking and fix `.gitignore`. Rewriting history (`git filter-repo`) is optional once the key is revoked. A revoked key in history is harmless.

Rotation is also good hygiene without a leak. If you know how to swap a key in five minutes, a leak costs you five minutes.

## 5. Secrets on hosting platforms and in CI

Every platform has a place for environment variables, kept outside your repo:

- **Railway:** the service's *Variables* tab. Changes are *staged* and take effect when you deploy them. A variable can be *sealed*: it's still given to builds and deploys, but it's never shown again in the UI. One service can reference another's variable, e.g. `DATABASE_URL=${{Postgres.DATABASE_URL}}`.
- **Render:** the service's *Environment* page, where you add variables or a secret file. When you save, you choose *Save, rebuild, and deploy*, *Save and deploy*, or *Save only*.
- **GitHub Actions:** *Settings → Secrets and variables → Actions*, read in a workflow as `${{ secrets.ANTHROPIC_API_KEY }}`. Actions masks secret values in logs.

Use **separate keys per environment**: one for local development, one for CI, one for production. Then a key leaked from a laptop doesn't touch production, and you can see in the Console which environment is spending money. Give production its own Anthropic workspace with a spend limit if you can.

What must never happen: secrets in the Dockerfile (`ENV ANTHROPIC_API_KEY=...`), in `docker-compose.yml` committed to git, in front-end JavaScript, in log lines, or in error messages returned to users.

## 6. A health-check endpoint

Platforms need a URL to ask "is this instance OK?". Railway calls it before switching traffic to a new deploy. Render calls it during deploys and keeps calling it while the service runs, restarting an instance that stays unhealthy. Uptime monitors call it every minute. It's two small endpoints:

```python
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def create_app(check_db: Callable[[], bool], version: str = "dev") -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": version}

    @app.get("/ready")
    def ready() -> JSONResponse:
        try:
            db_ok = bool(check_db())
        except Exception:
            db_ok = False
        if db_ok:
            return JSONResponse({"status": "ok", "checks": {"database": "ok"}})
        return JSONResponse({"status": "unavailable", "checks": {"database": "error"}}, status_code=503)

    return app
```

- **Liveness (`/health`)** answers "is the process alive?". It must be fast and depend on nothing. If it checked the database and the database blipped, the platform would restart perfectly healthy app instances, making things worse.
- **Readiness (`/ready`)** answers "can I serve real traffic?". It checks the things a request needs: here, a `SELECT 1` against Postgres. Failure returns **503**, and an exception becomes a 503 rather than a 500 crash.
- **Don't call Claude in a health check.** It costs money on every poll, and an Anthropic outage would mark your app as dead when it could still serve cached answers or a friendly error.
- **Return the version** (a git commit SHA from an env var like `GIT_SHA`) so you can confirm which code is live.
- **No authentication** on these routes: the platform can't send your API key, and they reveal nothing sensitive.

A real `check_db` with a psycopg pool:

```python
def check_db() -> bool:
    with pool.connection(timeout=2) as conn:
        conn.execute("SELECT 1")
    return True
```

Which one do you give the platform? Use `/ready` as the deploy health check when your app can't work without its database: the new version only receives traffic once it can actually connect. Use `/health` for anything that restarts instances on failure.

## Common mistakes

- **Committing `.env`.** Create `.gitignore` first. If it happened, revoke the key; removing the file isn't enough.
- **Reading `os.environ` all over the code.** One `Settings` model, loaded once, passed around as a dependency.
- **Lazy validation.** A setting checked on first use fails in production, hours after a "successful" deploy. Validate at startup.
- **Treating `"false"` as false.** `bool("false")` is `True`. Let Pydantic parse booleans (`"false"`, `"0"`, `"no"` all become `False`).
- **Printing settings with plain `str` secrets.** Use `SecretStr`.
- **One key everywhere.** Separate keys for dev, CI and production limit the damage and make spend visible.
- **A health check that calls the database or Claude on the liveness route,** so a dependency blip restarts every instance.

## Recap

- Config that varies per deploy goes in environment variables; code doesn't change between environments.
- A Pydantic `Settings` model converts and validates every variable, and `SecretStr` keeps keys out of logs. Load it at startup so a bad config stops the deploy.
- `.env` is for local development only, loaded with `load_dotenv()`, git-ignored from the first commit; commit `.env.example`.
- A leaked key: revoke first, then replace, redeploy, check usage.
- On Railway, Render and GitHub Actions, secrets go in the platform's variables or secrets settings, with separate keys per environment.
- `/health` (liveness, no dependencies) and `/ready` (readiness, checks the database, 503 on failure) give platforms and monitors something to poll.
