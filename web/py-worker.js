// Runs Python exercises in the browser (web version), using Pyodide.
// Mirrors engine/runner.py: learner code is solution.py, hidden tests are tests.py, and the
// harness runs every test_* function in file order and prints one JSON line after a marker.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pyodide.js");

const MARKER = "__LEARN_RESULTS__";
const HARNESS = `
import json, traceback, inspect, os
NAMES = {"solution.py": "your code", "tests.py": "test"}
def describe(e):
    if isinstance(e, AssertionError):
        head = str(e) or "Assertion failed"
    elif isinstance(e, SyntaxError):
        return "".join(traceback.format_exception_only(e)).replace(os.getcwd() + os.sep, "").strip()
    else:
        head = f"{type(e).__name__}: {e}"
    frames = [f for f in traceback.extract_tb(e.__traceback__) if os.path.basename(f.filename) in NAMES]
    where = [f"  {NAMES[os.path.basename(f.filename)]}, line {f.lineno}: {(f.line or '').strip()}" for f in frames[-3:]]
    return "\\n".join([head, *where])
results = []
try:
    import tests
except BaseException as e:
    results.append({"name": "import", "passed": False, "error": describe(e)})
else:
    fns = [f for n, f in vars(tests).items() if n.startswith("test_") and callable(f)]
    fns.sort(key=lambda f: inspect.getsourcelines(f)[1])
    for f in fns:
        try:
            f()
            results.append({"name": f.__name__, "passed": True, "error": ""})
        except BaseException as e:
            results.append({"name": f.__name__, "passed": False, "error": describe(e)})
print("\\n${MARKER}" + json.dumps(results))
`;

// Browsers give Python no threads, and FastAPI's TestClient starts one. This drop-in calls the app
// in-process through httpx's ASGITransport instead, so FastAPI exercise tests run unchanged.
const WEB_TESTCLIENT = `
import asyncio, contextlib
try:
    import httpx  # only installed when the exercise uses it (FastAPI exercises)
except ImportError:
    httpx = None

class WebTestClient:
    def __init__(self, app, base_url="http://testserver", raise_server_exceptions=True, headers=None, cookies=None, follow_redirects=True, **_):
        self.app, self.base_url = app, base_url
        self.raise_server_exceptions, self.follow_redirects = raise_server_exceptions, follow_redirects
        self.headers, self.cookies = dict(headers or {}), dict(cookies or {})
    def __enter__(self): return self
    def __exit__(self, *exc): return False
    def request(self, method, url, **kw):
        kw.setdefault("follow_redirects", self.follow_redirects)
        async def go():
            transport = httpx.ASGITransport(app=self.app, raise_app_exceptions=self.raise_server_exceptions)
            async with httpx.AsyncClient(transport=transport, base_url=self.base_url, headers=self.headers, cookies=self.cookies) as client:
                response = await client.request(method, url, **kw)
                await response.aread()
                return response
        return asyncio.run(go())
    def get(self, url, **kw): return self.request("GET", url, **kw)
    def post(self, url, **kw): return self.request("POST", url, **kw)
    def put(self, url, **kw): return self.request("PUT", url, **kw)
    def patch(self, url, **kw): return self.request("PATCH", url, **kw)
    def delete(self, url, **kw): return self.request("DELETE", url, **kw)
    def options(self, url, **kw): return self.request("OPTIONS", url, **kw)
    def head(self, url, **kw): return self.request("HEAD", url, **kw)
    @contextlib.contextmanager
    def stream(self, method, url, **kw):
        yield self.request(method, url, **kw)

# FastAPI runs plain "def" endpoints and dependencies in a thread pool. No threads here, so run them inline.
try:
    import anyio.to_thread as _to_thread
    async def _run_sync(func, *args, abandon_on_cancel=False, cancellable=None, limiter=None):
        return func(*args)
    _to_thread.run_sync = _run_sync
except Exception:
    pass

for _name in (("starlette.testclient", "fastapi.testclient") if httpx else ()):
    try:
        _mod = __import__(_name, fromlist=["TestClient"])
        _mod.TestClient = WebTestClient
    except Exception:
        pass
`;

let pyodide = null;
const installed = new Map();  // requirement -> true (installed) or error text
const status = (text) => postMessage({ type: "status", text });

// The import name of a requirement, when it differs from the package name.
const ALIASES = { "python-dotenv": "dotenv", "beautifulsoup4": "bs4", "pyyaml": "yaml", "scikit-learn": "sklearn", "pillow": "PIL", "opencv-python": "cv2" };
const importName = (req) => { const n = req.match(/^[A-Za-z0-9._-]+/)[0].toLowerCase(); return ALIASES[n] || n.replace(/-/g, "_"); };

// Only install the requirements this exercise imports: a word-count exercise shouldn't wait for numpy and FastAPI.
async function ready(requirements, sources) {
  if (!pyodide) {
    status("Loading Python in your browser (first time only, about 10 MB)…");
    pyodide = await loadPyodide();
    await pyodide.loadPackage(["micropip", "sqlite3"]);  // sqlite3 is a separate package in Pyodide
  }
  const imports = new Set();
  const find = pyodide.pyimport("pyodide.code").find_imports;
  for (const src of sources) { try { for (const m of find(src).toJs()) imports.add(m.toLowerCase()); } catch (e) { /* syntax error: the run reports it */ } }
  if (imports.has("fastapi") || imports.has("starlette")) imports.add("httpx");  // the test client runs on httpx
  const need = [...requirements, ...(imports.has("httpx") && !requirements.some((r) => importName(r) === "httpx") ? ["httpx"] : [])]
    .filter((r) => !installed.has(r) && imports.has(importName(r).toLowerCase()));
  if (need.length) {
    status(`Installing ${need.join(", ")} (first time only)…`);
    const micropip = pyodide.pyimport("micropip");
    for (const r of need) {
      for (let attempt = 0; attempt < 4; attempt++) {
        try { await micropip.install(r); installed.set(r, true); break; }
        catch (e) {
          const msg = String(e);
          // "Requested 'typing-extensions>=4.15.0', but typing-extensions==4.14.1 is already installed":
          // upgrade the package Pyodide preloaded, then try again.
          const clash = msg.match(/Requested '([^']+)', but ([\w.-]+)==[^ ]+ is already installed/);
          if (clash && attempt < 3) {
            try { micropip.uninstall(clash[2]); await micropip.install(clash[1]); continue; } catch (e2) { /* fall through */ }
          }
          installed.set(r, msg.split("\n").filter(Boolean).slice(-1)[0].slice(0, 300));
          break;
        }
      }
    }
  }
}

let runs = 0;
self.onmessage = async ({ data }) => {
  const { mode, code, tests, support, requirements } = data;
  let stdout = "", stderr = "";
  try {
    const sources = [code, mode === "run" ? "" : tests, ...Object.entries(support || {}).filter(([n]) => n.endsWith(".py")).map(([, t]) => t)];
    await ready(requirements || [], sources);
    if (mode === "warm") return void postMessage({ type: "done", stdout: "", stderr: "", exit_code: 0, timed_out: false });
    postMessage({ type: "started" });
    pyodide.setStdout({ batched: (s) => { stdout += s + "\n"; } });
    pyodide.setStderr({ batched: (s) => { stderr += s + "\n"; } });
    const dir = `/home/pyodide/run${++runs}`;
    pyodide.FS.mkdirTree(dir);
    const files = { "solution.py": code, ...(mode === "check" ? { "tests.py": tests } : {}), ...support };
    for (const [name, text] of Object.entries(files)) pyodide.FS.writeFile(`${dir}/${name}`, text);
    pyodide.globals.set("_RUN_DIR", dir);
    pyodide.globals.set("_MODE", mode);
    pyodide.globals.set("_HARNESS", HARNESS);
    pyodide.globals.set("_WEB_TESTCLIENT", WEB_TESTCLIENT);
    pyodide.globals.set("_MODULES", ["solution", "tests", ...Object.keys(support).filter((n) => n.endsWith(".py")).map((n) => n.slice(0, -3))]);
    const exitCode = await pyodide.runPythonAsync(`
import os, sys, runpy, traceback
os.chdir(_RUN_DIR)
sys.path = [p for p in sys.path if not p.startswith("/home/pyodide/run")]
sys.path.insert(0, _RUN_DIR)
for m in list(_MODULES):
    sys.modules.pop(m, None)
_code = 0
try:
    exec(compile(_WEB_TESTCLIENT, "_web_testclient.py", "exec"), {"__name__": "_web_testclient"})
    if _MODE == "check":
        exec(compile(_HARNESS, "_harness.py", "exec"), {"__name__": "__main__"})
    else:
        runpy.run_path("solution.py", run_name="__main__")
except SystemExit as e:
    _code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
except BaseException:
    traceback.print_exc()
    _code = 1
_code
`);
    const missing = [...installed].filter(([, v]) => v !== true);
    if (missing.length && /ModuleNotFoundError/.test(stdout + stderr)) {
      stderr += `\nNote: the web version couldn't install ${missing.map(([k]) => k).join(", ")} (${missing.map(([, v]) => v).join("; ").slice(0, 300)}). This exercise needs the downloaded LearnPack to run.`;
    }
    postMessage({ type: "done", stdout, stderr, exit_code: exitCode, timed_out: false });
  } catch (e) {
    postMessage({ type: "done", stdout, stderr: stderr + String(e), exit_code: 1, timed_out: false });
  }
};
