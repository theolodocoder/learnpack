import json
from pathlib import Path

from engine.webbuild import build_web

ROOT = Path(__file__).resolve().parent.parent


def test_build_web_versions_files_and_bundles_packs(tmp_path):
    out = tmp_path / "site"
    ids = build_web(out, ROOT / "courses")
    assert "ai-engineering" in ids and "_template" not in ids
    # Every deploy gets a fresh build id, so browsers and the offline cache never mix old and new files.
    for name in ("runner.js", "sw.js"):
        assert 'const BUILD = "dev"' not in (out / name).read_text()
    assert 'app.js?v=' in (out / "index.html").read_text()
    pack = json.loads((out / "packs" / "ai-engineering.json").read_text())
    assert pack["_bundle"] == 1 and pack["sections"]
