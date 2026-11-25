"""Build the web version: the same app as static files, with each course pack as one JSON bundle.

  python3 server.py build-web site/            every pack in courses/ (not _template), ready to host
  python3 server.py bundle courses/x x.json   one shareable pack file people can drag into the web version
"""
import base64
import json
import time
import shutil
from pathlib import Path

from engine.pack import COVER_TYPES, cover_files, lessons, list_packs, load_pack, validate_pack

ROOT = Path(__file__).resolve().parent.parent
SUPPORT_EXT = {".py", ".js", ".mjs", ".ts", ".json", ".txt", ".csv"}


def bundle(pack_dir: Path, embed_cover: bool = True) -> dict:
    """A pack as a single JSON object: all files resolved, plus support files, the add-on stylesheet and the cover."""
    pack_dir = Path(pack_dir)
    problems = validate_pack(pack_dir)
    if problems:
        raise ValueError(f"{pack_dir} has problems:\n  " + "\n  ".join(problems))
    course = load_pack(pack_dir)
    support = {}
    if course.get("support"):
        for f in sorted((pack_dir / course["support"]).iterdir()):
            if f.is_file() and f.suffix in SUPPORT_EXT:
                support[f.name] = f.read_text(encoding="utf-8")
    course["_support"] = support
    css = course.get("theme", {}).get("css")
    if css:
        course["_themeCss"] = (pack_dir / css).read_text(encoding="utf-8")
    if embed_cover:  # a shared bundle has no server behind it, so the card cover travels inside it
        course["_cover"] = {m: f"data:{COVER_TYPES[f.suffix.lower()]};base64,{base64.b64encode(f.read_bytes()).decode()}"
                            for m, f in cover_files(course, pack_dir).items()} or None
    course["_bundle"] = 1
    return course


def summary(course: dict) -> dict:
    return {"id": course["id"], "title": course["title"], "description": course.get("description", ""),
            "accent": course.get("theme", {}).get("accent"), "total": sum(1 for _ in lessons(course))}


def build_web(out: Path, courses_dir: Path = ROOT / "courses") -> list[str]:
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "web", out)
    (out / ".nojekyll").write_text("")  # serve files as-is on GitHub Pages
    # Version the scripts so browsers fetch fresh copies after each deploy instead of stale cached ones.
    build_id = str(int(time.time()))
    for name in ("runner.js", "sw.js"):
        f = out / name
        f.write_text(f.read_text().replace('const BUILD = "dev"', f'const BUILD = "{build_id}"'))
    index = out / "index.html"
    html = index.read_text()
    for name in ("style.css", "study.js", "local.js", "runner.js", "app.js"):
        html = html.replace(f'"{name}"', f'"{name}?v={build_id}"')
    index.write_text(html)
    (out / "packs").mkdir()
    index = []
    for pack in list_packs(courses_dir):
        course = bundle(pack, embed_cover=False)
        (out / "packs" / f"{course['id']}.json").write_text(json.dumps(course, ensure_ascii=False), encoding="utf-8")
        cover = {}
        for mode, f in cover_files(course, pack).items():  # served as files, so the home page stays light
            name = f"{course['id']}-cover-{mode}{f.suffix.lower()}"
            shutil.copyfile(f, out / "packs" / name)
            cover[mode] = f"packs/{name}"
        index.append({**summary(course), "cover": cover or None})
    (out / "packs" / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return [c["id"] for c in index]
