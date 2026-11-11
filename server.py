"""Local learning platform.

  python3 server.py [--port 8000]        serve every course pack in courses/
  python3 server.py validate <pack-dir>  check a pack and run its reference solutions
"""
import argparse
import json
import os
import re
import secrets
import sys
import tempfile
import time
import urllib.request
import webbrowser
from html import unescape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from engine.pack import (ID_RE, PackError, find_practice, lessons, list_packs, load_pack,
                         practice_items, practice_lang, public_course, validate_pack)
from engine.runner import check_code, run_code

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
STATIC_TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml"}


class App:
    def __init__(self, courses_dir: Path, data_dir: Path, token: str):
        self.courses_dir, self.data_dir, self.token = Path(courses_dir), Path(data_dir), token

    def packs(self) -> dict:
        # Reloaded on every request so edits to a pack show up on refresh.
        return {load_pack(p)["id"]: p for p in list_packs(self.courses_dir)}

    def course(self, cid):
        pack = self.packs().get(cid)
        return (load_pack(pack), pack) if pack else (None, None)

    def file(self, cid, kind, item_id, ext) -> Path:
        return self.data_dir / cid / kind / f"{item_id}{ext}"

    def note_files(self, cid, nid):
        d = self.data_dir / cid / "notes"
        return d / f"{nid}.html", d / f"{nid}.md"

    def list_notes(self, cid) -> list:
        d = self.data_dir / cid / "notes"
        if not d.is_dir():
            return []
        out = []
        for f in d.iterdir():
            if f.suffix == ".html" or (f.suffix == ".md" and not f.with_suffix(".html").exists()):
                raw = f.read_text()
                out.append({"id": f.stem, "modified": int(f.stat().st_mtime * 1000),
                            "text": plain_text(raw) if f.suffix == ".html" else raw})
        return sorted(out, key=lambda n: -n["modified"])

    def state(self, cid) -> dict:
        p = self.data_dir / cid / "state.json"
        try:
            return json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            return {"done": [], "checklist": {}, "links": {}, "last": ""}


def plain_text(html: str) -> str:
    """Note HTML -> plain text, one line per block. Used for titles, previews and search."""
    s = re.sub(r"<(br|/div|/p|/li|/h[1-6]|/pre)\b[^>]*>", "\n", html, flags=re.I)
    s = unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ")
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())


def write_atomic(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def make_handler(app: App, port: int):
    allowed_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="application/json", headers=None):
            data = body if isinstance(body, bytes) else (
                json.dumps(body) if ctype == "application/json" else body).encode()
            self.send_response(code)
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def body(self) -> bytes:
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))

        def guard(self) -> bool:
            # Blocks other websites (CSRF) and DNS rebinding from reaching the code runner.
            if self.headers.get("Host") not in allowed_hosts:
                self.send(403, {"error": "bad host"})
                return False
            if self.path.startswith("/api/") and self.headers.get("X-Learn-Token") != app.token:
                self.send(403, {"error": "bad token"})
                return False
            return True

        def do_GET(self):
            self.route("GET")

        def do_PUT(self):
            self.route("PUT")

        def do_POST(self):
            self.route("POST")

        def do_DELETE(self):
            self.route("DELETE")

        def note(self, method, cid, nid):
            html_f, md_f = app.note_files(cid, nid)
            if method == "GET":
                if html_f.is_file():
                    return self.send(200, html_f.read_text(), "text/html", {"X-Note-Format": "html"})
                if md_f.is_file():  # notes written before rich text; the browser converts them
                    return self.send(200, md_f.read_text(), "text/plain", {"X-Note-Format": "md"})
                return self.send(200, "", "text/html", {"X-Note-Format": "html"})
            if method == "PUT":
                html = self.body().decode("utf-8")
                if not plain_text(html).strip():  # like Apple Notes: an empty note disappears
                    html_f.unlink(missing_ok=True)
                else:
                    write_atomic(html_f, html)
                md_f.unlink(missing_ok=True)
                return self.send(200, {"ok": True})
            if method == "DELETE":
                trash = html_f.parent / ".trash"
                trash.mkdir(parents=True, exist_ok=True)
                for f in (html_f, md_f):
                    if f.is_file():
                        os.replace(f, trash / f"{f.stem}-{int(time.time())}{f.suffix}")
                return self.send(200, {"ok": True})
            self.send(405, {"error": "method"})

        def route(self, method):
            if not self.guard():
                return
            path = urlparse(self.path).path
            try:
                if not path.startswith("/api/"):
                    return self.static(path) if method == "GET" else self.send(405, {"error": "method"})
                parts = [unquote(p) for p in path.split("/")[2:] if p]
                if parts[1:] and not all(ID_RE.match(p) for p in parts[1:]):
                    return self.send(404, {"error": "not found"})
                return self.api(method, parts)
            except PackError as e:
                self.send(500, {"error": str(e)})

        def static(self, path):
            if path in ("/", "/index.html"):
                html = (WEB / "index.html").read_text().replace("__TOKEN__", app.token)
                return self.send(200, html, "text/html")
            m = re.fullmatch(r"/packs/([a-z0-9-]+)/theme\.css", path)
            if m:  # a pack's add-on stylesheet (theme.css in course.json); plain CSS, no token needed
                course, pack = app.course(m[1])
                css = (course or {}).get("theme", {}).get("css")
                if css and (pack / css).resolve().is_relative_to(pack.resolve()) and (pack / css).is_file():
                    return self.send(200, (pack / css).read_bytes(), "text/css")
                return self.send(404, "not found", "text/plain")
            f = (WEB / path.lstrip("/")).resolve()
            if f.is_relative_to(WEB) and f.is_file() and f.suffix in STATIC_TYPES:
                return self.send(200, f.read_bytes(), STATIC_TYPES[f.suffix])
            self.send(404, "not found", "text/plain")

        def api(self, method, parts):
            if parts == ["courses"] and method == "GET":
                out = []
                for cid, pack in app.packs().items():
                    c = load_pack(pack)
                    total = sum(1 for _ in lessons(c))
                    done = len(set(app.state(cid)["done"]) & {l["id"] for _, l in lessons(c)})
                    out.append({"id": cid, "title": c["title"], "description": c.get("description", ""),
                                "accent": c.get("theme", {}).get("accent"), "total": total, "done": done})
                return self.send(200, out)
            if len(parts) < 2 or parts[0] != "courses":
                return self.send(404, {"error": "not found"})
            course, pack = app.course(parts[1])
            if not course:
                return self.send(404, {"error": "no such course"})
            cid, rest = parts[1], parts[2:]

            if not rest and method == "GET":
                return self.send(200, public_course(course))
            if rest == ["state"]:
                if method == "GET":
                    return self.send(200, app.state(cid))
                if method == "PUT":
                    state = json.loads(self.body())
                    write_atomic(app.data_dir / cid / "state.json", json.dumps(state, indent=2))
                    return self.send(200, {"ok": True})
            if rest == ["notes"] and method == "GET":
                return self.send(200, app.list_notes(cid))
            if len(rest) == 2 and rest[0] == "notes":
                return self.note(method, cid, rest[1])
            if len(rest) == 2 and rest[0] == "code":
                f = app.file(cid, "code", rest[1], ".py")
                if method == "GET":
                    if f.is_file():
                        return self.send(200, f.read_text(), "text/plain")
                    p = find_practice(course, rest[1])
                    return self.send(200, (p or {}).get("starter", ""), "text/plain")
                if method == "PUT":
                    write_atomic(f, self.body().decode("utf-8"))
                    return self.send(200, {"ok": True})
            if len(rest) == 2 and rest[0] == "solution" and method == "GET":
                p = find_practice(course, rest[1])
                return self.send(200, {"solution": p["solution"]}) if p and "solution" in p else self.send(404, {})
            if rest == ["run"] and method == "POST":
                req = json.loads(self.body())
                p = find_practice(course, str(req.get("practice", "")))
                if not p or p.get("type") != "code":
                    return self.send(404, {"error": "no such practice"})
                support = pack / course["support"] if course.get("support") else None
                code = str(req.get("code", ""))
                lang = practice_lang(course, p)
                if req.get("mode") == "check":
                    return self.send(200, check_code(code, p["tests"], support_dir=support, lang=lang))
                return self.send(200, run_code(code, support_dir=support, lang=lang))
            self.send(404, {"error": "not found"})

    return Handler


def serve(port: int, courses_dir=ROOT / "courses", data_dir=ROOT / "learner-data", token=None):
    app = App(courses_dir, data_dir, token or secrets.token_urlsafe(24))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), BaseHTTPRequestHandler)
    httpd.RequestHandlerClass = make_handler(app, httpd.server_address[1])  # real port when port=0
    return httpd, app


def validate(pack_dir: Path) -> int:
    problems = validate_pack(pack_dir)
    for p in problems:
        print("✗", p)
    if problems:
        return 1
    course = load_pack(pack_dir)
    support = pack_dir / course["support"] if course.get("support") else None
    failed = 0
    for p in practice_items(course):
        if p["type"] != "code":
            continue
        r = check_code(p["solution"], p["tests"], support_dir=support, lang=practice_lang(course, p))
        bad = [t for t in r["results"] if not t["passed"]]
        print("✗" if bad else "✓", p["id"], *(f"\n    {t['name']}: {t['error'].strip()}" for t in bad))
        failed += bool(bad)
    print(f"\n{len(list(lessons(course)))} lessons, {failed} failing practice item(s)")
    return 1 if failed else 0


def already_running(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return "LEARN_TOKEN" in r.read(4096).decode("utf-8", "ignore")
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="serve", choices=["serve", "validate"])
    ap.add_argument("pack", nargs="?")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true", help="don't open the browser")
    a = ap.parse_args()
    if a.command == "validate":
        if not a.pack:
            ap.error("validate needs a pack folder")
        sys.exit(validate(Path(a.pack)))
    url = f"http://localhost:{a.port}"
    try:
        httpd, _ = serve(a.port)
    except OSError:
        if already_running(url):  # double-clicked again: reuse the running app
            print(f"Already running at {url}")
            webbrowser.open(url)
            return
        sys.exit(f"Port {a.port} is busy with something else. Try: python3 server.py --port 8001")
    print(f"Learning platform running at {url}\nKeep this window open while you study. Close it (or press Ctrl+C) to stop.")
    if not a.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
