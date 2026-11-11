import json
from pathlib import Path

import pytest

from engine.pack import PackError, load_pack, public_course, validate_pack

ROOT = Path(__file__).resolve().parent.parent


def make_pack(tmp_path, course, files=None):
    (tmp_path / "course.json").write_text(json.dumps(course))
    for name, text in (files or {}).items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return tmp_path


def course_with(lesson=None, **extra):
    lesson = lesson or {"id": "l1", "title": "L1", "body": "hi"}
    return {"id": "c", "title": "C", "description": "d",
            "sections": [{"id": "s1", "title": "S1", "summary": "", "status": "ready", "lessons": [lesson]}], **extra}


def test_inline_and_file_fields_resolve(tmp_path):
    pack = make_pack(tmp_path, course_with({"id": "l1", "title": "L1", "body": {"file": "lessons/l1.md"}}),
                     {"lessons/l1.md": "# From file"})
    course = load_pack(pack)
    assert course["sections"][0]["lessons"][0]["body"] == "# From file"


def test_file_outside_pack_rejected(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    (tmp_path / "secret.txt").write_text("nope")
    make_pack(pack, course_with({"id": "l1", "title": "L1", "body": {"file": "../secret.txt"}}))
    with pytest.raises(PackError):
        load_pack(pack)


def test_duplicate_ids_reported(tmp_path):
    c = course_with()
    c["sections"][0]["lessons"].append({"id": "l1", "title": "dup", "body": "x"})
    assert any("duplicate" in p for p in validate_pack(make_pack(tmp_path, c)))


def test_bad_id_reported(tmp_path):
    assert any("id" in p for p in validate_pack(make_pack(tmp_path, course_with({"id": "../x", "title": "t", "body": "b"}))))


def test_quiz_answer_out_of_range_reported(tmp_path):
    lesson = {"id": "l1", "title": "L", "body": "b", "practice": [
        {"id": "q1", "type": "quiz", "question": "?", "options": ["a", "b"], "answer": 5, "explanation": ""}]}
    assert any("answer" in p for p in validate_pack(make_pack(tmp_path, course_with(lesson))))


def test_public_course_strips_tests_and_solution(tmp_path):
    lesson = {"id": "l1", "title": "L", "body": "b", "practice": [
        {"id": "p1", "type": "code", "title": "P", "prompt": "do", "starter": "", "tests": "T", "solution": "S"}]}
    pub = public_course(load_pack(make_pack(tmp_path, course_with(lesson))))
    item = pub["sections"][0]["lessons"][0]["practice"][0]
    assert "tests" not in item and "solution" not in item and item["prompt"] == "do"


def test_template_pack_is_valid():
    assert validate_pack(ROOT / "courses" / "_template") == []


def test_include_loads_section_file(tmp_path):
    c = course_with()
    c["sections"] = [{"include": "sections/s1.json"}]
    pack = make_pack(tmp_path, c, {"sections/s1.json": json.dumps(
        {"id": "s1", "title": "S1", "lessons": [{"id": "l1", "title": "L", "body": {"file": "l1.md"}}]}), "l1.md": "body!"})
    assert load_pack(pack)["sections"][0]["lessons"][0]["body"] == "body!"
    assert validate_pack(pack) == []


def test_new_fields_validated(tmp_path):
    c = course_with(format=2, language="ruby", features={"notes": True, "teleport": True}, theme={"accent": "red", "css": "missing.css"})
    probs = " | ".join(validate_pack(make_pack(tmp_path, c)))
    for word in ("format", "language", "teleport", "accent", "missing.css"):
        assert word in probs, (word, probs)
