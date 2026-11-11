# A tiny Dockerfile linter

Write `lint_dockerfile(text: str) -> list[str]` that reads a Dockerfile and returns the **sorted** list of problem codes it finds (each code at most once; `[]` if it's clean).

Parsing:

- An instruction is the first word of a line (`FROM`, `RUN`, `COPY`, …), case-insensitive; the rest is its arguments.
- A line ending in `\` continues on the next line: join them before checking.
- Skip blank lines and lines starting with `#`.

Rules:

| Code | Flag it when |
|---|---|
| `latest-tag` | a `FROM` image has no tag (`FROM python`) or uses `:latest`. Ignore flags like `--platform=...`; `FROM python:3.12-slim AS builder` is fine. |
| `no-user` | the final stage never switches to a non-root user: after the **last** `FROM` there is no `USER`, or the last `USER` is `root` or `0`. Every `FROM` starts a new stage that runs as root again. |
| `pip-cache` | a `RUN` contains `pip install` without `--no-cache-dir`. |
| `copy-before-install` | `COPY . <dest>` (copying the whole folder, source `.` or `./`) happens **before the first** dependency install (`RUN` containing `pip install`, `uv sync` or `uv pip install`). A second install after the copy is fine (that's the uv pattern). `COPY --from=...` never counts. |
| `localhost-bind` | a `CMD` or `ENTRYPOINT` contains `127.0.0.1` or `localhost`. |

## Example

```python
bad = """
FROM python
COPY . /app
RUN pip install -r /app/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1"]
"""
lint_dockerfile(bad)
# ['copy-before-install', 'latest-tag', 'localhost-bind', 'no-user', 'pip-cache']
```

Each rule is one of the real mistakes from the *Docker for AI apps* lesson. Real linters such as hadolint check dozens more.
