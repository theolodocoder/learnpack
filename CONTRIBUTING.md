# Contributing to LearnPack

Thanks for helping. Contributions come in two kinds, and both are welcome:

- **Platform:** the app itself (`server.py`, `engine/`, `web/`): bugs, features, docs.
- **Course packs:** new courses, or fixes to the included ones. See [docs/writing-packs.md](docs/writing-packs.md).

## Development setup

```bash
git clone https://github.com/theolodocoder/learnpack.git
cd learnpack
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
python3 server.py --no-browser      # http://localhost:8000
```

Python 3.10+ is required, plus Node 24+ for the JS/TS runner and its tests. There's no build step: edit a file and refresh the browser. Restart the server after changing Python files.

## Tests

Run all three before opening a pull request. CI runs them too.

```bash
.venv/bin/python -m pytest -q              # server API, pack loader/validator, code runner (Python + JS/TS)
node --test tests/study.test.js            # streaks, review schedule, timer phases
for p in courses/*/; do python3 server.py validate "$p" || exit 1; done   # every pack, every solution
```

Add a test with every behaviour change:
- **Engine:** `tests/test_*.py`
- **Pure front-end logic:** `web/study.js` + `tests/study.test.js`

## Architecture

```
web/                         browser app: plain HTML/CSS/JS, no framework, no build
├── index.html               shell; libraries from cdnjs (marked, DOMPurify, CodeMirror 5, highlight.js)
├── app.js                   routing, rendering, notes, editor, timer, focus mode, review
├── study.js                 pure logic (dates, streaks, review schedule); also loaded by Node tests
└── style.css                design tokens on :root (light/dark), then components
server.py                    HTTP server + JSON API + CLI (serve / validate); standard library only
engine/
├── pack.py                  load_pack (resolves {"file"} and {"include"}), validate_pack, public_course
└── runner.py                run_code / check_code for python, javascript, typescript
courses/<id>/                course packs (see docs/pack-format.md)
learner-data/<id>/           per-learner data, git-ignored: state.json, notes/*.html, code/*
```

**Request flow**
1. The page loads with a per-launch token injected.
2. Every `/api/` call sends `X-Learn-Token` and must come from `localhost`/`127.0.0.1` (the Host header is checked).
3. Course content is reloaded from disk on each request, so editing a pack shows up after a refresh.
4. `public_course()` strips `tests` and `solution` before anything reaches the browser.

**Running code**
- **Where it runs:** `runner.py` writes the learner's code to a temp folder as `solution.<ext>`, alongside the exercise's `tests.<ext>` and a small harness.
- **How it runs:** in a subprocess, with a 60-second timeout.
- **Python harness:** calls every `test_*` function in file order.
- **JS/TS harness:** defines a global `test()`, imports the tests, then runs them.
- **Reporting:** results come back as one JSON line after a marker, so the learner's own output is kept separate.
- **Python environment:** the course's `.venv` if it exists, so exercises can import real packages.
- **Support folder:** goes on `PYTHONPATH` (Python), or is copied next to the code (JS/TS, because ES modules ignore `NODE_PATH`).

**State**
- **Progress:** a single JSON document per course (`state.json`), written atomically.
- **Notes:** one HTML file per note. An empty note is deleted; a deleted note moves to `notes/.trash/`.
- **Saved code:** one file per exercise.

## Principles

- **Simple to run:** no database, no accounts, no build tools, no runtime dependencies for the platform.
- **The pack configures the course.** No settings screens; features and look come from `course.json`.
- **Learning first:** new UI must earn its place on screen. Prefer less.
- **Never lose learner work:** don't save over files that failed to load, and show save failures.
- **Secure by default:** the code runner must stay unreachable from other websites (see [SECURITY.md](SECURITY.md)).

## Pull requests

1. Open an issue first for anything bigger than a fix, so we can agree on the approach.
2. Keep pull requests focused, with tests, and update the docs if behaviour changes.
3. For pack content: run `validate`, and verify every new video id and link (see [docs/writing-packs.md](docs/writing-packs.md#writing-a-pack-with-ai)).

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE) (platform code) or the licence declared in the pack you're changing (pack content).
