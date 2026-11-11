def _instructions(text: str) -> list[tuple[str, str]]:
    """Join backslash continuations, drop comments and blanks, return (INSTRUCTION, args) pairs."""
    out, buf = [], ""
    for raw in text.splitlines():
        line = raw.strip()
        if not buf and (not line or line.startswith("#")):
            continue
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        line, buf = buf + line, ""
        word, _, args = line.partition(" ")
        out.append((word.upper(), args.strip()))
    return out


def _is_install(args: str) -> bool:
    return "pip install" in args or "uv sync" in args or "uv pip install" in args


def lint_dockerfile(text: str) -> list[str]:
    problems = set()
    user = None
    copied_everything = False
    installed = False
    for instr, args in _instructions(text):
        if instr == "FROM":
            words = [w for w in args.split() if not w.startswith("--")]
            image = words[0] if words else ""
            name = image.rsplit("/", 1)[-1]
            if image.lower() != "scratch" and "@" not in image and (":" not in name or name.endswith(":latest")):
                problems.add("latest-tag")
            user = None  # each stage starts as root again
        elif instr == "USER":
            user = args.split(":")[0]
        elif instr == "COPY":
            words = [w for w in args.split() if not w.startswith("--")]
            if not args.startswith("--from") and words and words[0] in (".", "./"):
                copied_everything = True
        elif instr == "RUN":
            if "pip install" in args and "--no-cache-dir" not in args:
                problems.add("pip-cache")
            if _is_install(args):
                if copied_everything and not installed:
                    problems.add("copy-before-install")
                installed = True
        elif instr in ("CMD", "ENTRYPOINT"):
            if "127.0.0.1" in args or "localhost" in args:
                problems.add("localhost-bind")
    if user in (None, "root", "0"):
        problems.add("no-user")
    return sorted(problems)


if __name__ == "__main__":
    bad = """
FROM python
COPY . /app
RUN pip install -r /app/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1"]
"""
    print(lint_dockerfile(bad))
    # ['copy-before-install', 'latest-tag', 'localhost-bind', 'no-user', 'pip-cache']
