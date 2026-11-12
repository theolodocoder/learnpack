"""Load and validate course packs. A pack is a folder with course.json (see course.schema.json)."""
import copy
import json
import re
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
FORMAT = 1  # the pack format this engine reads; bump on breaking changes
LANGUAGES = ("python", "javascript", "typescript")
# Interface features a pack can switch off. Learners can switch them off too, in Settings.
FEATURES = ("notes", "timer", "focusMode", "studyStats", "review", "browser")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def practice_lang(course: dict, p: dict) -> str:
    return p.get("language") or course.get("language") or "python"
TEXT_FIELDS = {"description", "summary", "body", "prompt", "starter", "tests", "solution", "brief", "question", "explanation"}


class PackError(Exception):
    pass


def _read(pack_dir: Path, rel: str) -> str:
    path = (pack_dir / rel).resolve()
    if not path.is_relative_to(pack_dir.resolve()):
        raise PackError(f"file outside pack: {rel}")
    if not path.is_file():
        raise PackError(f"missing file: {rel}")
    return path.read_text(encoding="utf-8")


def _resolve(node, pack_dir: Path):
    """Replace every {"file": ...} text field with the file's contents."""
    if isinstance(node, list):
        return [_resolve(x, pack_dir) for x in node]
    if isinstance(node, dict):
        if set(node) == {"include"}:  # {"include": "sections/x.json"} splits big courses into files
            try:
                return _resolve(json.loads(_read(pack_dir, node["include"])), pack_dir)
            except json.JSONDecodeError as e:
                raise PackError(f"{node['include']}: {e}") from e
        out = {}
        for k, v in node.items():
            if k in TEXT_FIELDS and isinstance(v, dict) and set(v) == {"file"}:
                out[k] = _read(pack_dir, v["file"])
            else:
                out[k] = _resolve(v, pack_dir)
        return out
    return node


def load_pack(pack_dir: Path) -> dict:
    pack_dir = Path(pack_dir)
    try:
        raw = json.loads((pack_dir / "course.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise PackError(f"course.json: {e}") from e
    return _resolve(raw, pack_dir)


def lessons(course: dict):
    for s in course.get("sections", []):
        for l in s.get("lessons", []):
            yield s, l


def practice_items(course: dict):
    for _, l in lessons(course):
        yield from l.get("practice", [])


def find_practice(course: dict, practice_id: str):
    return next((p for p in practice_items(course) if p.get("id") == practice_id), None)


def find_lesson(course: dict, lesson_id: str):
    return next((l for _, l in lessons(course) if l.get("id") == lesson_id), None)


def validate_pack(pack_dir: Path) -> list[str]:
    try:
        course = load_pack(pack_dir)
    except PackError as e:
        return [str(e)]
    problems = []
    seen = set()

    def need(obj, where, *keys):
        for k in keys:
            if k not in obj:
                problems.append(f"{where}: missing '{k}'")

    def check_id(obj, where):
        i = obj.get("id")
        if not isinstance(i, str) or not ID_RE.match(i):
            problems.append(f"{where}: bad id {i!r} (use lowercase letters, digits, dashes)")
        elif i in seen:
            problems.append(f"{where}: duplicate id {i!r}")
        else:
            seen.add(i)

    need(course, "course", "id", "title", "sections")
    check_id(course, "course")
    if course.get("format", FORMAT) != FORMAT:
        problems.append(f"course: format {course.get('format')!r} isn't supported; this engine reads format {FORMAT}")
    if course.get("language", "python") not in LANGUAGES:
        problems.append(f"course: language must be one of {', '.join(LANGUAGES)}")
    for k, v in (course.get("features") or {}).items():
        if k not in FEATURES or not isinstance(v, bool):
            problems.append(f"course: features.{k} isn't a known feature ({', '.join(FEATURES)}) set to true/false")
    theme = course.get("theme") or {}
    if "accent" in theme and not COLOR_RE.match(str(theme["accent"])):
        problems.append("course: theme.accent must be a colour like #E4471B")
    if "css" in theme:
        try:
            _read(Path(pack_dir), theme["css"])
        except PackError as e:
            problems.append(f"course: theme.css: {e}")
    for s in course.get("sections", []):
        sw = f"section {s.get('id')}"
        check_id(s, sw)
        need(s, sw, "title")
        if s.get("status", "ready") not in ("ready", "coming-soon"):
            problems.append(f"{sw}: status must be 'ready' or 'coming-soon'")
        for l in s.get("lessons", []):
            lw = f"lesson {l.get('id')}"
            check_id(l, lw)
            need(l, lw, "title", "body")
            for v in l.get("videos", []):
                if not (v.get("youtube") or v.get("playlist")):
                    problems.append(f"{lw}: video needs 'youtube' or 'playlist'")
            for r in l.get("resources", []):
                if not str(r.get("url", "")).startswith(("http://", "https://")):
                    problems.append(f"{lw}: resource url must be http(s)")
            for p in l.get("practice", []):
                pw = f"practice {p.get('id')}"
                check_id(p, pw)
                if p.get("type") == "code":
                    need(p, pw, "title", "prompt", "starter", "tests", "solution")
                    if practice_lang(course, p) not in LANGUAGES:
                        problems.append(f"{pw}: language must be one of {', '.join(LANGUAGES)}")
                elif p.get("type") == "quiz":
                    need(p, pw, "question", "options", "answer")
                    if not (isinstance(p.get("answer"), int) and 0 <= p["answer"] < len(p.get("options", []))):
                        problems.append(f"{pw}: answer must be an index into options")
                else:
                    problems.append(f"{pw}: type must be 'code' or 'quiz'")
        if "project" in s:
            pr = s["project"]
            need(pr, f"project in {sw}", "title", "brief")
            if not isinstance(pr.get("checklist", []), list):
                problems.append(f"project in {sw}: checklist must be a list")
    return problems


def public_course(course: dict) -> dict:
    """What the browser may see: no hidden tests or reference solutions."""
    pub = copy.deepcopy(course)
    for p in practice_items(pub):
        if p.get("type") == "code":
            p.pop("tests", None)
            p.pop("solution", None)
    return pub


def list_packs(courses_dir: Path) -> list[Path]:
    return sorted(p for p in Path(courses_dir).iterdir()
                  if p.is_dir() and not p.name.startswith("_") and (p / "course.json").is_file())
