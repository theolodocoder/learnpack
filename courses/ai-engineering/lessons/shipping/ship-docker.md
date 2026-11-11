# Docker for AI apps

## Why this matters

"It works on my machine" stops being a joke the first time you deploy. The server has a different OS, a different Python, and none of the packages you installed six weeks ago and forgot about. A Docker image packages your app with its exact Python version and dependencies, so what you test on your Mac is what runs on Railway, Render, or a client's server. Most AI gigs that say "deploy it" mean "give me a container".

## 1. Images and containers

Two words you need to keep apart:

- An **image** is a read-only package: a filesystem (a minimal Linux, Python, your dependencies, your code) plus metadata such as which command to run. You build it once. It has a name and tag, like `docs-chat:1.0`.
- A **container** is a running instance of an image: a process with its own isolated filesystem, network and environment variables. You can start many containers from one image, stop them, delete them, and the image is unchanged.

The relationship is like a class and its objects, or a program file and the processes running it. Containers aren't virtual machines: they share the host's kernel, so they start in well under a second and add almost no overhead. On a Mac, Docker Desktop runs a small Linux VM in the background and your containers run inside it.

An image is built in **layers**. Each instruction in a `Dockerfile` adds one, and Docker caches layers: if an instruction and everything before it are unchanged, Docker reuses the cached layer instead of re-running it. That one fact decides how you order a Dockerfile.

Check Docker works:

```bash
docker version                       # client and server versions
docker run --rm hello-world          # pulls a tiny image, runs it, deletes the container
```

## 2. The project you're containerising

The files below assume a uv-managed FastAPI project laid out like the section projects:

```
docs-chat/
├── pyproject.toml        # dependencies, including "fastapi[standard]"
├── uv.lock               # exact versions: commit this
├── app/
│   ├── __init__.py
│   └── main.py           # app = FastAPI(...), with GET /health
└── tests/
```

`fastapi[standard]` includes `uvicorn`, the server that runs the app. If you used `pip` and `requirements.txt` instead, section 6 shows that variant.

## 3. A production Dockerfile with uv

Save this as `Dockerfile` (capital D, no extension) in the project root:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install uv by copying its binary from the official image. Pin the version.
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app

# 1) Dependencies only. Cached until pyproject.toml or uv.lock change.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# 2) Your code. Changes often, so it comes after the slow step.
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Use the virtual environment uv created.
ENV PATH="/app/.venv/bin:$PATH"

# 3) Don't run as root.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Line by line:

- **`FROM python:3.12-slim`**: the base image. `slim` is Debian with only what Python needs, about a fifth the size of the full `python:3.12` image. Pin the Python version to match `requires-python` in your `pyproject.toml`. Avoid `alpine` for Python: it uses a different C library, so many wheels (numpy, psycopg) won't install from binaries and builds become slow or break.
- **`COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/`**: copies the uv binary out of Astral's published image. This is the method the uv docs recommend. Pinning a version means a new uv release can't change your build overnight.
- **`ENV ...`**:
  - `PYTHONUNBUFFERED=1` makes `print` and logs appear immediately in `docker logs`, not in delayed chunks.
  - `UV_COMPILE_BYTECODE=1` compiles `.pyc` files at build time, so the container starts faster.
  - `UV_LINK_MODE=copy` avoids a warning when uv's cache and the venv are on different filesystems.
  - `UV_NO_DEV=1` skips dev dependencies like pytest.
- **`WORKDIR /app`**: creates `/app` and makes it the current directory for everything after.
- **The two-step install is the layer-caching trick.** Dependencies change rarely; your code changes on every build. Copying only `pyproject.toml` and `uv.lock` first means the expensive `uv sync` layer stays cached when you edit `main.py`. Rebuilds take seconds instead of minutes.
  - `--no-install-project` installs the dependencies without your own code, which isn't copied yet.
  - `--locked` fails the build if `uv.lock` is out of date with `pyproject.toml`, so the image always has exactly the versions you tested.
- **`RUN --mount=type=cache,...`**: a BuildKit cache mount. uv's download cache survives between builds without being stored in the image. It's the uv equivalent of pip's `--no-cache-dir`: a small image and fast rebuilds.
- **`ENV PATH=...`**: puts `.venv/bin` first, so `uvicorn` and `python` mean the venv's copies.
- **`USER appuser`**: by default a container runs as root. If someone finds a bug in your app that lets them run commands (a real risk for an agent with tools), root inside the container makes everything easier for them. A normal user costs one line.
- **`EXPOSE 8000`**: documentation only. It doesn't publish the port; `-p` does that.
- **`CMD`**: the command a container runs on start.
  - **`--host 0.0.0.0`** listens on every network interface. Uvicorn's default, `127.0.0.1`, only accepts connections from *inside the container*, so nothing outside could reach it.
  - **`--port ${PORT:-8000}`**: Railway and Render tell your app which port to use through the `PORT` variable. `${PORT:-8000}` means "`$PORT`, or 8000 if it isn't set".
  - **Why `sh -c`?** The JSON ("exec") form of `CMD` doesn't run a shell, so `$PORT` would be passed literally. `sh -c` expands it.
  - **Why `exec`?** It replaces the shell with uvicorn, so uvicorn gets the stop signal when the platform shuts the container down and can finish in-flight requests.

> **Note:** FastAPI's docs use `CMD ["fastapi", "run", "app/main.py", "--port", "80"]`. `fastapi run` is uvicorn with production defaults (it listens on `0.0.0.0`). Either works; the version above adds `$PORT`.

## 4. `.dockerignore`

`docker build .` sends the whole folder (the *build context*) to Docker, and `COPY . .` copies all of it into the image. Without a `.dockerignore`, that includes your local `.venv` (built for macOS, useless and huge in a Linux image), your `.git` history, and your **`.env` with real keys**. Anyone who pulls the image could read them.

```
# .dockerignore
.venv
.env
.env.*
!.env.example
.git
.gitignore
__pycache__
*.pyc
.pytest_cache
.ruff_cache
.DS_Store
Dockerfile
docker-compose.yml
```

## 5. Build, run, inspect

```bash
docker build -t docs-chat .              # build an image named docs-chat from the current folder
docker images                            # list images
docker run --rm -p 8000:8000 --env-file .env docs-chat
```

- `-p 8000:8000` publishes the port as `host:container`: your Mac's port 8000 forwards to the container's port 8000. `-p 9000:8000` would make it `localhost:9000` on your Mac.
- `--env-file .env` passes your local variables in at run time. Secrets go in when the container *starts*, never into the image when it's *built*.
- `--rm` deletes the container when it stops.

In another terminal:

```bash
curl localhost:8000/health               # {"status":"ok","version":"dev"}
docker ps                                # running containers, with ids and names
docker logs -f <container-id>            # follow its output
docker exec -it <container-id> sh        # a shell inside the running container
whoami                                   # appuser (inside the container)
docker stop <container-id>
```

> **Try it:** Build once, change a line in `app/main.py`, and build again. The output marks the `uv sync --no-install-project` step `CACHED`. Then add a dependency with `uv add` and build again: that step re-runs.

> **Note:** `docker run --env-file` reads `KEY=value` lines literally: quotes are **not** stripped. `KEY="abc"` gives the value `"abc"` with the quote marks. Leave values unquoted in `.env` files you'll use with Docker.

## 6. The pip variant

If your project uses `requirements.txt`, the same ideas apply:

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home appuser
USER appuser
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

`--no-cache-dir` stops pip saving its download cache inside the image, where it would only add size.

## 7. Docker Compose: the app plus Postgres with pgvector

Your RAG backend needs Postgres with the pgvector extension. Compose runs several containers together from one file, on a private network where each service is reachable by its name.

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      DATABASE_URL: postgresql://app:devpassword@db:5432/docs
    depends_on:
      db:
        condition: service_healthy

  db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: docs
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d docs"]
      interval: 5s
      retries: 10

volumes:
  pgdata:
```

- **`db` is the hostname.** Inside the compose network, the API reaches Postgres at `db:5432`, not `localhost:5432`. `localhost` inside a container means that container itself. `environment:` overrides the `DATABASE_URL` from `.env`, which points at `localhost` for running the app directly on your Mac.
- **`depends_on` with `condition: service_healthy`** waits until `pg_isready` passes before starting the API. Plain `depends_on` only waits for the container to *start*, and Postgres takes a few seconds more to accept connections.
- **The named volume `pgdata`** keeps your data when containers are removed.
- **`pgvector/pgvector:pg17`** is Postgres 17 with pgvector already installed. You still run `CREATE EXTENSION IF NOT EXISTS vector;` once, at app startup.
- The development password is fine here because this file only runs on your machine. Production databases get generated credentials from the platform.

```bash
docker compose up --build        # build the api image, start both, stream logs (Ctrl+C stops)
docker compose up -d             # same, in the background
docker compose logs -f api       # follow one service's logs
docker compose exec db psql -U app -d docs    # a psql shell in the database
docker compose down              # stop and remove containers (data volume kept)
docker compose down -v           # ...and delete the data volume too
```

> **Note:** On your Mac, a container can reach a service running directly on the Mac (not in Docker) at `host.docker.internal` instead of `localhost`.

## Common mistakes

- **Listening on `127.0.0.1`.** The app starts, logs look fine, and every request from outside the container fails. Use `--host 0.0.0.0`.
- **Hard-coding the port.** Platforms assign one through `$PORT`. Use `${PORT:-8000}` through `sh -c`, because the exec form of `CMD` doesn't expand variables.
- **`COPY . .` before installing dependencies.** Every code change invalidates the cache and reinstalls everything. Copy the lock file, install, then copy the code.
- **No `.dockerignore`.** Your `.env` ends up inside the image and your macOS `.venv` overwrites the Linux one.
- **Secrets in the Dockerfile.** `ENV ANTHROPIC_API_KEY=...` or `ARG` values are stored in the image and visible with `docker history`. Pass secrets at run time.
- **Running as root.** Add a user and `USER` it.
- **`FROM python` or `:latest`.** The base can change under you. Pin `python:3.12-slim`.
- **pip without `--no-cache-dir`** (or uv without a cache mount): a bigger image for nothing.
- **`localhost` for the database inside compose.** Use the service name, `db`.
- **Building on an Apple Silicon Mac and pushing the image to an x86 server.** Images are built for your CPU architecture (`arm64`). Railway and Render build from your Dockerfile on their own machines, so this doesn't affect them. If you push a pre-built image to a registry, build with `docker build --platform linux/amd64 ...`.

## Recap

- An image is a built, read-only package; a container is a running instance of it. Layers are cached, so order instructions from least to most frequently changed.
- The uv Dockerfile: `python:3.12-slim`, uv copied from its official image, lock files copied and `uv sync --locked --no-install-project` first, code second, a cache mount, `.venv/bin` on `PATH`, a non-root user, and uvicorn on `0.0.0.0:${PORT:-8000}`.
- `.dockerignore` keeps `.env`, `.venv` and `.git` out of the image.
- `docker build -t name .`, `docker run -p host:container --env-file .env name`, and `docker logs` / `exec` / `ps` are the everyday commands.
- Compose runs the app and `pgvector/pgvector:pg17` together; services find each other by name, and a health-checked `depends_on` makes the app wait for the database.
