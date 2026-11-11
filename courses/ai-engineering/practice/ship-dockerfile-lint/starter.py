def lint_dockerfile(text: str) -> list[str]:
    """Return the sorted list of problem codes found in a Dockerfile.

    Codes: "copy-before-install", "latest-tag", "localhost-bind", "no-user", "pip-cache".
    """
    # TODO 1: turn the text into (INSTRUCTION, args) pairs:
    #         join lines ending in a backslash, skip blank lines and lines starting with '#'.
    # TODO 2: walk the instructions, tracking:
    #         - the current USER (reset at every FROM: each stage starts as root)
    #         - whether a COPY of "." (the whole folder) has happened yet
    #         - whether a dependency install (pip install / uv sync / uv pip install) has happened yet
    # TODO 3: apply each rule from the prompt and collect codes in a set; return sorted(codes).
    return []


if __name__ == "__main__":
    bad = """
FROM python
COPY . /app
RUN pip install -r /app/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1"]
"""
    print(lint_dockerfile(bad))
    # want: ['copy-before-install', 'latest-tag', 'localhost-bind', 'no-user', 'pip-cache']
