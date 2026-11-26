"""Run learner code with the real local Python (or Node), in a throwaway folder.

server.py calls run_code for the Run button and check_code for Check, which runs a practice
item's hidden tests through a small harness and returns one result per test. There is no sandbox:
this is the learner's own machine running their own code, bounded only by a timeout.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "__LEARN_RESULTS__"

# Runs every test_* function in tests.py in file order and prints one JSON line after MARKER.
HARNESS = f"""
import json, traceback, inspect, os

NAMES = {{"solution.py": "your code", "tests.py": "test"}}

def describe(e):
    # Short, path-free message: what failed, then where (in the learner's code or the test).
    if isinstance(e, AssertionError):
        head = str(e) or "Assertion failed"
    elif isinstance(e, SyntaxError):
        return "".join(traceback.format_exception_only(e)).replace(os.getcwd() + os.sep, "").strip()
    else:
        head = f"{{type(e).__name__}}: {{e}}"
    frames = [f for f in traceback.extract_tb(e.__traceback__) if os.path.basename(f.filename) in NAMES]
    where = [f"  {{NAMES[os.path.basename(f.filename)]}}, line {{f.lineno}}: {{(f.line or '').strip()}}" for f in frames[-3:]]
    return "\\n".join([head, *where])

results = []
try:
    import tests
except BaseException as e:
    results.append({{"name": "import", "passed": False, "error": describe(e)}})
else:
    fns = [f for n, f in vars(tests).items() if n.startswith("test_") and callable(f)]
    fns.sort(key=lambda f: inspect.getsourcelines(f)[1])
    for f in fns:
        try:
            f()
            results.append({{"name": f.__name__, "passed": True, "error": ""}})
        except BaseException as e:
            results.append({{"name": f.__name__, "passed": False, "error": describe(e)}})
print("\\n{MARKER}" + json.dumps(results))  # own line, even if the learner printed with end=""
"""


def python_bin() -> str:
    """The interpreter that runs learner code."""
    # The course's own environment if it exists (Mac/Linux, then Windows layout), else this Python.
    for venv in (ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "Scripts" / "python.exe"):
        if venv.exists():
            return str(venv)
    return sys.executable


def _env(support_dir) -> dict:
    """Environment for learner code: ours, plus keys from the project's .env (e.g. API keys), plus support_dir."""
    env = dict(os.environ)
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip("'\""))  # real environment variables win
    if support_dir:
        # Absolute: code runs from a temp folder, so a relative path would point nowhere.
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(Path(support_dir).resolve()), env.get("PYTHONPATH")]))
    env["PYTHONUNBUFFERED"] = "1"
    return env


# JavaScript/TypeScript run on Node (24+ runs .ts directly). Tests call a global
# test("name", fn) with node:assert; this harness runs them in order and prints one JSON line.
JS_HARNESS = f"""
const tests = [];
globalThis.test = (name, fn) => tests.push({{ name, fn }});
const NAMES = {{ solution: "your code", tests: "test" }};
function describe(e) {{
  const head = e && e.message ? `${{e.name === "AssertionError" ? "" : e.name + ": "}}${{e.message}}` : String(e);
  const where = String(e && e.stack || "").split("\\n")
    .map((l) => l.match(/\\/(solution|tests)\\.(?:js|ts):(\\d+):\\d+/)).filter(Boolean).slice(0, 3)
    .map((m) => `  ${{NAMES[m[1]]}}, line ${{m[2]}}`);
  return [head, ...where].join("\\n");
}}
const results = [];
try {{
  await import("./tests.EXT");
  for (const t of tests) {{
    try {{ await t.fn(); results.push({{ name: t.name, passed: true, error: "" }}); }}
    catch (e) {{ results.push({{ name: t.name, passed: false, error: describe(e) }}); }}
  }}
}} catch (e) {{
  results.push({{ name: "import", passed: false, error: describe(e) }});
}}
console.log("\\n{MARKER}" + JSON.stringify(results));
"""

LANGS = {"python": "py", "javascript": "js", "typescript": "ts"}


def _cmd(lang: str, script: str) -> list[str]:
    """The command line that runs script in lang."""
    if lang == "python":
        return [python_bin(), script]
    node = shutil.which("node")
    if not node:
        raise FileNotFoundError("Node.js is needed for JavaScript and TypeScript exercises: install it from nodejs.org")
    return [node, script]


def _exec(workdir: Path, script: str, support_dir, timeout, lang="python") -> dict:
    """Run script in workdir; {stdout, stderr, exit_code, timed_out}. A timeout kills the process."""
    try:
        proc = subprocess.run(_cmd(lang, script), cwd=workdir, env=_env(support_dir),
                              capture_output=True, text=True, timeout=timeout)
        return {"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        # Keep whatever was printed before the timeout; it can arrive as bytes despite text=True.
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return {"stdout": out, "stderr": f"Stopped: your code ran longer than {timeout} seconds.",
                "exit_code": None, "timed_out": True}
    except FileNotFoundError as e:  # no Node installed (raised by _cmd)
        return {"stdout": "", "stderr": str(e), "exit_code": None, "timed_out": False}


def _prepare(workdir: Path, lang: str, support_dir):
    """Set up workdir for JS/TS: treat files as ES modules and copy in the pack's support files."""
    if lang != "python":
        (workdir / "package.json").write_text('{"type": "module"}')
        if support_dir:  # ES modules ignore NODE_PATH, so copy helpers next to the code
            for f in Path(support_dir).resolve().glob("*"):
                if f.suffix in (".js", ".mjs", ".ts", ".json") and f.is_file():
                    shutil.copy(f, workdir / f.name)


def run_code(code: str, *, support_dir=None, timeout=60, lang="python") -> dict:
    """Run the learner's code as a script and return its output (see _exec)."""
    ext = LANGS[lang]
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        _prepare(workdir, lang, support_dir)
        (workdir / f"solution.{ext}").write_text(code)
        return _exec(workdir, f"solution.{ext}", support_dir, timeout, lang)


def check_code(code: str, tests: str, *, support_dir=None, timeout=60, lang="python") -> dict:
    """Run tests against the learner's code. Like run_code, plus results: [{name, passed, error}]."""
    ext = LANGS[lang]
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        _prepare(workdir, lang, support_dir)
        (workdir / f"solution.{ext}").write_text(code)
        (workdir / f"tests.{ext}").write_text(tests)
        if lang == "python":
            (workdir / "_harness.py").write_text(HARNESS)
            result = _exec(workdir, "_harness.py", support_dir, timeout)
        else:
            (workdir / f"_harness.{ext}").write_text(JS_HARNESS.replace("EXT", ext))
            result = _exec(workdir, f"_harness.{ext}", support_dir, timeout, lang)
    # The harness prints its JSON last; rpartition takes the last marker, so one the learner printed earlier is ignored.
    results = []
    out, sep, tail = result["stdout"].rpartition("\n" + MARKER)
    if sep:
        results = json.loads(tail.strip())
        result["stdout"] = out
    if not results:  # crashed or timed out before reporting: one failing result that says why
        results = [{"name": "tests", "passed": False,
                    "error": "Timed out" if result["timed_out"] else (result["stderr"] or "Tests did not run")}]
    result["results"] = results
    return result
