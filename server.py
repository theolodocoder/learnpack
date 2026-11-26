"""Local learning platform.

  python3 server.py [--port 8000]        serve every course pack in courses/
  python3 server.py validate <pack-dir>  check a pack and run its reference solutions
  python3 server.py build-web [site/]    build the web version (static files) into a folder
  python3 server.py bundle <pack-dir>    write one shareable .learnpack.json file for the web version
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
from urllib.parse import parse_qs, unquote, urlparse

from engine.pack import (COVER_TYPES, ID_RE, PackError, cover_files, find_practice, lessons, list_packs, load_pack,
                         practice_items, practice_lang, public_course, validate_pack)
from engine.browse import BrowseError, browse
from engine.runner import check_code, run_code

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
STATIC_TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".png": "image/png"}


class App:
    """Where courses and learner data live, plus the session token the browser must send."""

    def __init__(self, courses_dir: Path, data_dir: Path, token: str):
        self.courses_dir, self.data_dir, self.token = Path(courses_dir), Path(data_dir), token

    def packs(self) -> dict:
        # Reloaded on every request so edits to a pack show up on refresh.
        return {load_pack(p)["id"]: p for p in list_packs(self.courses_dir)}

    def course(self, cid):
        """(course dict, pack folder) for a course id, or (None, None)."""
        pack = self.packs().get(cid)
        return (load_pack(pack), pack) if pack else (None, None)

    def file(self, cid, kind, item_id, ext) -> Path:
        """Where a learner file is saved; ids are checked against ID_RE before they get here."""
        return self.data_dir / cid / kind / f"{item_id}{ext}"

    def note_files(self, cid, nid):
        """(html, md) paths for a note. Rich-text notes are .html; older notes may still be .md."""
        notes_dir = self.data_dir / cid / "notes"
        return notes_dir / f"{nid}.html", notes_dir / f"{nid}.md"

    def list_notes(self, cid) -> list:
        """Every note as {id, modified, text}, newest first. An .html note wins over an .md of the same id."""
        notes_dir = self.data_dir / cid / "notes"
        if not notes_dir.is_dir():
            return []
        out = []
        for path in notes_dir.iterdir():
            if path.suffix == ".html" or (path.suffix == ".md" and not path.with_suffix(".html").exists()):
                raw = path.read_text()
                out.append({"id": path.stem, "modified": int(path.stat().st_mtime * 1000),
                            "text": plain_text(raw) if path.suffix == ".html" else raw})
        return sorted(out, key=lambda n: -n["modified"])

    def state(self, cid) -> dict:
        """The learner's progress for a course; a fresh state if none is saved yet."""
        path = self.data_dir / cid / "state.json"
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return {"done": [], "checklist": {}, "links": {}, "last": ""}


def plain_text(html: str) -> str:
    """Note HTML -> plain text, one line per block. Used for titles, previews and search."""
    text = re.sub(r"<(br|/div|/p|/li|/h[1-6]|/pre)\b[^>]*>", "\n", html, flags=re.I)
    text = unescape(re.sub(r"<[^>]+>", "", text)).replace("\xa0", " ")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def write_atomic(path: Path, text: str):
    """Write via a temp file and rename, so a crash mid-write never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def make_handler(app: App, port: int):
    """The request handler class for this app: static files from web/, pack assets, and the JSON API."""
    allowed_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal quiet
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
                # Every id after the first segment becomes part of a file path, so only safe ids get through.
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
            m = re.fullmatch(r"/packs/([a-z0-9-]+)/cover-(light|dark)", path)
            if m:  # a pack's card cover (theme.cover in course.json); validated to stay inside the pack
                course, pack = app.course(m[1])
                f = cover_files(course, pack).get(m[2]) if course else None
                if f:
                    return self.send(200, f.read_bytes(), COVER_TYPES[f.suffix.lower()])
                return self.send(404, "not found", "text/plain")
            f = (WEB / path.lstrip("/")).resolve()  # resolve() + is_relative_to stops ../ escaping web/
            if f.is_relative_to(WEB) and f.is_file() and f.suffix in STATIC_TYPES:
                return self.send(200, f.read_bytes(), STATIC_TYPES[f.suffix])
            self.send(404, "not found", "text/plain")

        def api(self, method, parts):
            if parts == ["browse"] and method == "GET":  # in-app browser panel
                url = parse_qs(urlparse(self.path).query).get("url", [""])[0]
                try:
                    return self.send(200, browse(url))
                except BrowseError as e:
                    return self.send(400, {"error": str(e)})
            if parts == ["courses"] and method == "GET":
                out = []
                for cid, pack in app.packs().items():
                    info = load_pack(pack)
                    total = sum(1 for _ in lessons(info))
                    done = len(set(app.state(cid)["done"]) & {lesson["id"] for _, lesson in lessons(info)})
                    out.append({"id": cid, "title": info["title"], "description": info.get("description", ""),
                                "accent": info.get("theme", {}).get("accent"), "total": total, "done": done,
                                "cover": {mode: f"/packs/{cid}/cover-{mode}" for mode in cover_files(info, pack)} or None})
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
                    practice = find_practice(course, rest[1])
                    return self.send(200, (practice or {}).get("starter", ""), "text/plain")
                if method == "PUT":
                    write_atomic(f, self.body().decode("utf-8"))
                    return self.send(200, {"ok": True})
            if len(rest) == 2 and rest[0] == "solution" and method == "GET":
                practice = find_practice(course, rest[1])
                if practice and "solution" in practice:
                    return self.send(200, {"solution": practice["solution"]})
                return self.send(404, {})
            if rest == ["run"] and method == "POST":
                req = json.loads(self.body())
                practice = find_practice(course, str(req.get("practice", "")))
                if not practice or practice.get("type") != "code":
                    return self.send(404, {"error": "no such practice"})
                support = pack / course["support"] if course.get("support") else None
                code = str(req.get("code", ""))
                lang = practice_lang(course, practice)
                if req.get("mode") == "check":  # hidden tests run here and never reach the browser
                    return self.send(200, check_code(code, practice["tests"], support_dir=support, lang=lang))
                return self.send(200, run_code(code, support_dir=support, lang=lang))
            self.send(404, {"error": "not found"})

    return Handler


def serve(port: int, courses_dir=ROOT / "courses", data_dir=ROOT / "learner-data", token=None):
    """Create (not start) the server on 127.0.0.1 only. Returns (httpd, app); port=0 picks a free port."""
    app = App(courses_dir, data_dir, token or secrets.token_urlsafe(24))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), BaseHTTPRequestHandler)
    httpd.RequestHandlerClass = make_handler(app, httpd.server_address[1])  # real port when port=0
    return httpd, app


def validate(pack_dir: Path) -> int:
    """Check a pack's structure, then run each code item's reference solution against its tests. Exit code."""
    problems = validate_pack(pack_dir)
    for problem in problems:
        print("✗", problem)
    if problems:
        return 1
    course = load_pack(pack_dir)
    support = pack_dir / course["support"] if course.get("support") else None
    failed = 0
    for item in practice_items(course):
        if item["type"] != "code":
            continue
        result = check_code(item["solution"], item["tests"], support_dir=support, lang=practice_lang(course, item))
        bad = [t for t in result["results"] if not t["passed"]]
        print("✗" if bad else "✓", item["id"], *(f"\n    {t['name']}: {t['error'].strip()}" for t in bad))
        failed += bool(bad)
    print(f"\n{len(list(lessons(course)))} lessons, {failed} failing practice item(s)")
    return 1 if failed else 0


def already_running(url: str) -> bool:
    """Is LearnPack itself on this port? Its index page carries LEARN_TOKEN; other apps' pages don't."""
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return "LEARN_TOKEN" in resp.read(4096).decode("utf-8", "ignore")
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="serve", choices=["serve", "validate", "build-web", "bundle"])
    parser.add_argument("pack", nargs="?", help="pack folder (validate, bundle) or output folder (build-web)")
    parser.add_argument("out", nargs="?", help="output file for bundle")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="don't open the browser")
    args = parser.parse_args()
    if args.command == "build-web":
        from engine.webbuild import build_web
        out = Path(args.pack or "site")
        ids = build_web(out)
        print(f"Built the web version in {out}/ with: {', '.join(ids) or 'no courses'}")
        return
    if args.command == "bundle":
        from engine.webbuild import bundle
        if not args.pack:
            parser.error("bundle needs a pack folder")
        course = bundle(Path(args.pack))
        out = Path(args.out or f"{course['id']}.learnpack.json")
        out.write_text(json.dumps(course, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {out}: drag it into the web version to add the course")
        return
    if args.command == "validate":
        if not args.pack:
            parser.error("validate needs a pack folder")
        sys.exit(validate(Path(args.pack)))
    url = f"http://localhost:{args.port}"
    try:
        httpd, _ = serve(args.port)
    except OSError:
        if already_running(url):  # double-clicked again: reuse the running app
            print(f"Already running at {url}")
            if not args.no_browser:
                webbrowser.open(url)
            return
        sys.exit(f"Port {args.port} is busy with something else. Try: python3 server.py --port 8001")
    print(f"Learning platform running at {url}\nKeep this window open while you study. Close it (or press Ctrl+C) to stop.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
