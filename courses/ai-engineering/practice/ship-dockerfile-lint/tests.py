from solution import lint_dockerfile

GOOD = """
# syntax=docker/dockerfile:1
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev
COPY . .
RUN uv sync --locked --no-dev

RUN useradd --create-home appuser
USER appuser
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
"""


def check(text, want):
    got = lint_dockerfile(text)
    assert got == want, f"expected {want!r}, got {got!r}"


def test_good_dockerfile_has_no_problems():
    check(GOOD, [])


def test_flags_everything_in_a_bad_dockerfile():
    bad = """
FROM python
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
"""
    check(bad, ["copy-before-install", "latest-tag", "localhost-bind", "no-user", "pip-cache"])


def test_last_user_wins_and_root_counts_as_no_user():
    switched_back = GOOD.replace('CMD ["sh"', 'USER root\nCMD ["sh"')
    check(switched_back, ["no-user"])
    check(GOOD.replace("USER appuser", "USER 0"), ["no-user"])


def test_pip_with_no_cache_dir_and_requirements_first_is_fine():
    text = """
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER nobody
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
"""
    check(text, [])


def test_handles_continuations_comments_and_latest():
    text = """
FROM python:latest AS base
# a comment line with pip install in it should be ignored
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && \\
    pip install \\
      -r requirements.txt
COPY . .
USER app
ENTRYPOINT ["uvicorn", "main:app", \\
            "--host", "localhost"]
"""
    check(text, ["latest-tag", "localhost-bind", "pip-cache"])


def test_user_resets_in_each_build_stage():
    text = """
FROM python:3.12-slim AS builder
USER builder
RUN echo build
FROM python:3.12-slim
COPY --from=builder /app /app
CMD ["python", "/app/main.py"]
"""
    check(text, ["no-user"])
