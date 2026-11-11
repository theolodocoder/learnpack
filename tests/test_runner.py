from engine.runner import check_code, run_code


def test_run_prints_stdout():
    r = run_code("print('hi')", support_dir=None)
    assert r["stdout"].strip() == "hi" and r["exit_code"] == 0 and not r["timed_out"]


def test_run_timeout():
    r = run_code("while True: pass", support_dir=None, timeout=2)
    assert r["timed_out"]


def test_check_pass_and_fail_per_test():
    tests = "from solution import f\n\ndef test_a():\n    assert f() == 1\n\ndef test_b():\n    assert f() == 2, 'expected 2'\n"
    r = check_code("def f():\n    return 1\n", tests, support_dir=None)
    assert [(t["name"], t["passed"]) for t in r["results"]] == [("test_a", True), ("test_b", False)]
    assert "expected 2" in r["results"][1]["error"]


def test_check_syntax_error_reports_import_failure():
    r = check_code("def f(:\n", "from solution import f\n\ndef test_a():\n    assert f()\n", support_dir=None)
    assert r["results"][0]["name"] == "import" and not r["results"][0]["passed"]
    assert "SyntaxError" in r["results"][0]["error"]


def test_support_dir_on_pythonpath(tmp_path):
    (tmp_path / "helper.py").write_text("VALUE = 42\n")
    r = run_code("import helper; print(helper.VALUE)", support_dir=tmp_path)
    assert r["stdout"].strip() == "42"


def test_check_survives_print_without_newline():
    r = check_code("print('chunk', end='')\ndef f():\n    return 1\n", "from solution import f\n\ndef test_a():\n    assert f() == 1\n", support_dir=None)
    assert r["results"] == [{"name": "test_a", "passed": True, "error": ""}] and r["stdout"] == "chunk"


def test_relative_support_dir(tmp_path, monkeypatch):
    (tmp_path / "sup").mkdir()
    (tmp_path / "sup" / "helper.py").write_text("VALUE = 7\n")
    monkeypatch.chdir(tmp_path)
    assert run_code("import helper; print(helper.VALUE)", support_dir="sup")["stdout"].strip() == "7"


JS_TESTS = """import assert from "node:assert/strict";
import { add } from "./solution.EXT";
test("adds small numbers", () => { assert.equal(add(2, 3), 5); });
test("adds negatives", async () => { assert.equal(add(-1, 1), 0, "expected 0"); });
"""


def test_check_javascript_per_test():
    r = check_code("export const add = (a, b) => a + b + (a < 0 ? 1 : 0);\nconsole.log('hi');",
                   JS_TESTS.replace("EXT", "js"), lang="javascript")
    assert [(t["name"], t["passed"]) for t in r["results"]] == [("adds small numbers", True), ("adds negatives", False)]
    assert "expected 0" in r["results"][1]["error"] and r["stdout"].strip() == "hi"


def test_check_typescript():
    r = check_code("export function add(a: number, b: number): number { return a + b; }",
                   JS_TESTS.replace("EXT", "ts"), lang="typescript")
    assert all(t["passed"] for t in r["results"]), r


def test_js_syntax_error_reports_import_failure():
    r = check_code("export const add = (a, b) => {", JS_TESTS.replace("EXT", "js"), lang="javascript")
    assert r["results"][0]["name"] == "import" and "SyntaxError" in r["results"][0]["error"]


def test_run_javascript_and_timeout():
    assert run_code("console.log(1 + 1)", lang="javascript")["stdout"].strip() == "2"
    assert run_code("while (true) {}", lang="javascript", timeout=2)["timed_out"]


def test_js_support_files_are_importable(tmp_path):
    (tmp_path / "helper.js").write_text("export const VALUE = 9;")
    r = run_code('import { VALUE } from "./helper.js"; console.log(VALUE);', lang="javascript", support_dir=tmp_path)
    assert r["stdout"].strip() == "9"
