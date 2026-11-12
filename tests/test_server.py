import json
import shutil
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from server import serve

ROOT = Path(__file__).resolve().parent.parent
TOKEN = "t0k"


@pytest.fixture
def base(tmp_path):
    courses = tmp_path / "courses"
    shutil.copytree(ROOT / "courses" / "_template", courses / "demo")
    httpd, _ = serve(0, courses, tmp_path / "data", TOKEN)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def req(url, method="GET", data=None, token=TOKEN, host=None):
    r = urllib.request.Request(url, method=method, data=data)
    if token:
        r.add_header("X-Learn-Token", token)
    if host:
        r.add_header("Host", host)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_missing_token_403(base):
    assert req(base + "/api/courses", token=None)[0] == 403


def test_bad_host_403(base):
    assert req(base + "/api/courses", host="evil.com")[0] == 403


def test_state_roundtrip(base):
    s = {"done": ["first-lesson"], "checklist": {}, "links": {}, "last": "first-lesson"}
    assert req(base + "/api/courses/my-course/state", "PUT", json.dumps(s).encode())[0] == 200
    assert json.loads(req(base + "/api/courses/my-course/state")[1]) == s


def test_notes_roundtrip(base):
    req(base + "/api/courses/my-course/notes/first-lesson", "PUT", "my *note*".encode())
    assert req(base + "/api/courses/my-course/notes/first-lesson")[1] == "my *note*"


def test_code_defaults_to_starter(base):
    assert req(base + "/api/courses/my-course/code/add-two")[1].startswith("def add(a, b):")


def test_traversal_id_404(base):
    assert req(base + "/api/courses/my-course/notes/..%2F..%2Fetc")[0] == 404


def test_course_has_no_solutions(base):
    body = req(base + "/api/courses/my-course")[1]
    assert "return a + b" not in body and "test_small" not in body


def test_run_check(base):
    payload = json.dumps({"practice": "add-two", "code": "def add(a, b):\n    return a + b\n", "mode": "check"})
    r = json.loads(req(base + "/api/courses/my-course/run", "POST", payload.encode())[1])
    assert all(t["passed"] for t in r["results"]) and len(r["results"]) == 2


def test_notes_list_empty_and_delete(base):
    url = base + "/api/courses/my-course/notes"
    req(url + "/first-lesson", "PUT", b"<div>My title</div><div>second &amp; line</div>")
    notes = json.loads(req(url)[1])
    assert [(n["id"], n["text"]) for n in notes] == [("first-lesson", "My title\nsecond & line")]
    req(url + "/first-lesson", "PUT", b"<div><br></div>")  # emptied -> removed
    assert json.loads(req(url)[1]) == []
    req(url + "/note-x1", "PUT", b"<div>Free note</div>")
    assert req(url + "/note-x1", "DELETE")[0] == 200
    assert json.loads(req(url)[1]) == [] and req(url + "/note-x1")[1] == ""


def test_browse_rejects_local_and_needs_token(base):
    assert req(base + "/api/browse?url=http%3A%2F%2F127.0.0.1%2F")[0] == 400
    assert "network" in req(base + "/api/browse?url=http%3A%2F%2Flocalhost%2F")[1]
    assert req(base + "/api/browse?url=https%3A%2F%2Fexample.com", token=None)[0] == 403
