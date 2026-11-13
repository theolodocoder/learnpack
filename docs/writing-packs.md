# Writing course packs

A course pack is a folder that becomes a course. This guide covers writing one by hand or with AI, checking it, and sharing or selling it. Every field is listed in the [pack format reference](pack-format.md).

## The 10-minute version

```bash
cp -r courses/_template courses/my-topic
```

1. In `courses/my-topic/course.json`, set a unique `id` (e.g. `"my-topic"`), a `title` and a `description`.
2. Edit the lesson, exercise and quiz that are already there.
3. Run:

   ```bash
   python3 server.py validate courses/my-topic
   ```

4. Refresh the browser. Your course appears in the course switcher.

You don't need to restart the app while you write: packs reload on every page load.

## How a good pack is structured

```
Course
└── Sections            one per milestone or week (4–8 lessons each)
    ├── Lessons         one topic each: written lesson + 0–3 videos + links + practice
    │   └── Practice    1–3 code exercises and 1–2 quizzes per lesson
    └── Project         one per section: proves the section's skills in a real build
```

**Lessons** should teach fully on their own page. Videos are companions, not the lesson. A pattern that works:

1. **Why this matters:** two to four concrete sentences.
2. **The concepts, step by step,** each with a short runnable example.
3. **Common mistakes.**
4. **A short recap.**

Aim for 1,200–2,500 words. Put tips in `> **Try it:** …` and `> **Note:** …` blockquotes.

**Exercises** are where learning happens:
- **Name exact functions.** Give the exact function names and signatures, with an example input and output.
- **Starters must run.** Every starter must run without crashing (placeholders, not errors).
- **3–6 tests per exercise.** Cover the normal case and at least one edge case.
- **Readable test names.** Learners see them: `test_rejects_negative_age` reads as "rejects negative age".
- **Tests are offline and deterministic.** No network, and no real API calls; put a fake client in `support/`, like `courses/ai-engineering/support/fake_llm.py`. Inject clocks instead of sleeping.

**Projects** prove a skill end to end. Give a brief (goal, requirements, a step-by-step plan, stretch goals) and a checklist of 6–12 concrete deliverables. Set `"links": true` when the project lives in its own repo.

## Exercise languages

| `language` | Runs with | Test style |
|---|---|---|
| `python` (default) | The course `.venv`, else system Python | `test_*` functions with `assert`; `from solution import …` |
| `javascript` | Node 24+ | Global `test("name", fn)` with `node:assert`; `import … from "./solution.js"` |
| `typescript` | Node 24+ (runs `.ts` directly) | Same, with `./solution.ts`. Erasable syntax only: no `enum`, no `namespace` |

Set the course default with `"language"` in `course.json`; any exercise can override it. In JS/TS tests, use the platform's global `test()`, not `node:test`'s. `node:test`'s `mock.timers` is fine for fake time.

## Look and features

Turn off interface features your course doesn't need, and give it its own colour:

```json
"features": { "timer": false, "review": false },
"theme": { "accent": "#0F766E", "css": "theme.css" }
```

`theme.css` loads after the platform's styles. Override the design tokens (`--accent`, `--radius`, `--font-body`, `--bg`, `--ink` …) or anything else.

## Writing a pack with AI

AI assistants are good at drafting packs, and the validator catches what they get wrong. A workflow that works:

1. **Research and roadmap first.** Ask the AI to find and vet sources for the topic, then produce a trimmed roadmap: sections → lessons → key concepts → exercise ideas → projects.
   - Ask it to give every source a verdict (trust / use parts / ignore) and to say why.
   - Ask it to list what it cut, and why, so the course stays focused.
2. **Give it the contract:** [`pack-format.md`](pack-format.md), [`course.schema.json`](../course.schema.json), one finished section from an included pack as an example, and this guide's quality rules.
3. **One section at a time.** Have it write each section's JSON, lessons, exercises and project, then run `validate` and fix every ✗ before moving on.
4. **Verify every link and video yourself.** AIs invent plausible YouTube ids and URLs.
   - Check each video:
     ```bash
     curl -s "https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v=ID"
     ```
     It must return JSON, and the title and channel must make sense.
   - Check each link:
     ```bash
     curl -s -o /dev/null -w '%{http_code}' -L URL
     ```
     It must print `200`. Also make sure the page title is the page you meant: some docs sites return 200 for pages that don't exist.
5. **Read the lessons.** The validator checks that the code works, not that the teaching is good.

## Checking a pack

```bash
python3 server.py validate courses/my-topic
```

- **Errors (✗) mean the pack is broken:** a missing file, a duplicate or badly formed id, a quiz answer that isn't one of the options, an unknown feature, a bad colour.
- **Every exercise is run.** Its reference solution must pass its own tests, or that exercise shows ✗ with the failing test and message.
- **Exit code `0` means ready to share,** so you can use `validate` in CI.

## Sharing and selling packs

A pack is just a folder, so you can distribute it however you like: a git repo, a zip, a download from a store.

**For learners:** unzip the pack into `courses/`, start the app, and pick the course from the switcher.

**For the web version:** turn the pack into one file and send that:

```bash
python3 server.py bundle courses/your-course your-course.learnpack.json
```

Learners drag the file (or a `.zip` of the pack folder) onto the home page of the [web version](https://theolodocoder.github.io/learnpack/). It's stored in their browser, nothing is uploaded. Python exercises install `requirements` with micropip, so pure-Python packages work; packages with native code that Pyodide doesn't ship, and Node-only APIs such as `node:crypto`, don't. Test your pack there before you share it.

**Before you publish:**
- **Fill in the pack's details:** `version`, `author`, `license` and `requirements` in `course.json`.
- **Validate it,** with a clean `validate` run.
- **Don't change ids after release.** Learner progress is keyed by ids, so renaming a lesson or exercise id resets everyone's progress for it. Bump `version` for content changes.
- **Choose a licence for your writing.** Free packs often use `CC-BY-4.0`; paid packs can use `"proprietary"` with your own terms.
- **Link, don't copy.** Videos and articles belong to their creators. Embed or link them; never re-host or paste their content. What you sell is your curation, your writing, your exercises and your projects.

**Trust:** a pack's exercises run as real code on the learner's machine. Say so on your store page, and only install packs from people you trust. See [SECURITY.md](../SECURITY.md).
