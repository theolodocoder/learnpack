"""Run learner code with the real local Python, in a throwaway folder."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "__LEARN_RESULTS__"

# Runs every test_* function in tests.py in file order and prints one JSON line.
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
    # The course's own environment if it exists (Mac/Linux, then Windows layout), else this Python.
    for venv in (ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "Scripts" / "python.exe"):
        if venv.exists():
            return str(venv)
    return sys.executable


def _env(support_dir) -> dict:
    env = dict(os.environ)
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip("'\""))
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
    if lang == "python":
        return [python_bin(), script]
    node = shutil.which("node")
    if not node:
        raise FileNotFoundError("Node.js is needed for JavaScript and TypeScript exercises: install it from nodejs.org")
    return [node, script]


def _exec(workdir: Path, script: str, support_dir, timeout, lang="python") -> dict:
    try:
        p = subprocess.run(_cmd(lang, script), cwd=workdir, env=_env(support_dir),
                           capture_output=True, text=True, timeout=timeout)
        return {"stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        return {"stdout": out, "stderr": f"Stopped: your code ran longer than {timeout} seconds.",
                "exit_code": None, "timed_out": True}
    except FileNotFoundError as e:
        return {"stdout": "", "stderr": str(e), "exit_code": None, "timed_out": False}


def _prepare(d: Path, lang: str, support_dir):
    if lang != "python":
        (d / "package.json").write_text('{"type": "module"}')
        if support_dir:  # ES modules ignore NODE_PATH, so copy helpers next to the code
            for f in Path(support_dir).resolve().glob("*"):
                if f.suffix in (".js", ".mjs", ".ts", ".json") and f.is_file():
                    shutil.copy(f, d / f.name)


def run_code(code: str, *, support_dir=None, timeout=60, lang="python") -> dict:
    ext = LANGS[lang]
    with tempfile.TemporaryDirectory() as d:
        _prepare(Path(d), lang, support_dir)
        Path(d, f"solution.{ext}").write_text(code)
        return _exec(Path(d), f"solution.{ext}", support_dir, timeout, lang)


def check_code(code: str, tests: str, *, support_dir=None, timeout=60, lang="python") -> dict:
    ext = LANGS[lang]
    with tempfile.TemporaryDirectory() as d:
        _prepare(Path(d), lang, support_dir)
        Path(d, f"solution.{ext}").write_text(code)
        Path(d, f"tests.{ext}").write_text(tests)
        if lang == "python":
            Path(d, "_harness.py").write_text(HARNESS)
            r = _exec(Path(d), "_harness.py", support_dir, timeout)
        else:
            Path(d, f"_harness.{ext}").write_text(JS_HARNESS.replace("EXT", ext))
            r = _exec(Path(d), f"_harness.{ext}", support_dir, timeout, lang)
    results = []
    out, sep, tail = r["stdout"].rpartition("\n" + MARKER)
    if sep:
        results = json.loads(tail.strip())
        r["stdout"] = out
    if not results:
        results = [{"name": "tests", "passed": False,
                    "error": "Timed out" if r["timed_out"] else (r["stderr"] or "Tests did not run")}]
    r["results"] = results
    return r
