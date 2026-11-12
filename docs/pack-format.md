# Course pack format (v1)

A **course pack** is a folder that turns this platform into a course. Drop the folder into `courses/`, refresh, and learners get the full interface for it: lessons, videos, practice with checked answers, notes, projects, progress, the focus timer and review.

Everything about a course (its content, its look, which features it has) is configured in the pack. There is no settings screen in the app.

- Machine-readable schema: [`course.schema.json`](../course.schema.json)
- Smallest working pack: [`courses/_template/`](../courses/_template/)
- Check a pack: `python3 server.py validate courses/<id>`. This checks the structure, then runs every exercise's reference solution against its tests.

## Folder layout

```
courses/my-course/
├── course.json              ← required: the whole course is described from here
├── theme.css                ← optional add-on stylesheet
├── sections/                ← optional: split big courses into one file per section
│   └── basics.json
├── lessons/
│   └── basics/first-lesson.md
├── practice/
│   └── add-two/
│       ├── prompt.md        ← the task the learner sees
│       ├── starter.py       ← code the learner starts from (.py / .js / .ts)
│       ├── tests.py         ← hidden tests behind the Check button
│       └── solution.py      ← reference answer behind "Show solution"
├── projects/basics.md
└── support/                 ← optional helpers available to exercise code (fakes, fixtures)
```

Only `course.json` is required. Any other layout works too, as long as `course.json` points at the files.

Two rules make that flexible:
- **Text can be inline or a file.** Any text or code field is either a string or `{"file": "path/inside/pack"}`.
- **Objects can live in their own files.** Any object can be replaced by `{"include": "path/to/other.json"}`.

So a whole course can be a single JSON file, which is handy when a tool or an AI generates it. A big course can also be split across hundreds of files, which is handier when people write it by hand.

## The structure

```
course
├── format, id, title, description, version, author, license
├── language, requirements          ← what exercises run in and need installed
├── features                        ← which interface features this course has
├── theme  { accent, css }          ← how it looks
├── support                         ← folder of helpers for exercise code
└── sections[]
    ├── id, title, summary, status ("ready" | "coming-soon")
    ├── lessons[]
    │   ├── id, title, duration
    │   ├── videos[]      { youtube | playlist, title, start }
    │   ├── body          Markdown (the written lesson)
    │   ├── resources[]   { title, url }
    │   └── practice[]
    │       ├── { type: "code", id, title, prompt, starter, tests, solution, language?, needs_api_key? }
    │       └── { type: "quiz", id, question, options[], answer, explanation }
    └── project           { id, title, brief, checklist[], links }
```

## Top level (`course.json`)

| Field | Required | What it does |
|---|---|---|
| `format` | recommended | Pack format version. This engine reads `1` and refuses packs written for a format it doesn't understand. |
| `id` | yes | Unique id, `lowercase-with-dashes`. It also names the learner's data folder. |
| `title`, `description` | yes / recommended | Shown on the course card and dashboard. |
| `version` | recommended | The pack's own version (`1.2.0`). Bump it when you publish changes. |
| `author` | recommended | `{ "name": "...", "url": "..." }` |
| `license` | recommended | Licence for your own written content, e.g. `CC-BY-4.0` or `proprietary`. Linked videos and docs keep their owners' terms; packs link to them and never copy them. |
| `language` | no | Default language for code exercises: `python` (default), `javascript` or `typescript`. Each exercise can override it. |
| `requirements` | no | What learners must install. `{ "python": ["fastapi", ...], "node": ">=24" }` |
| `features` | no | Turns interface features off for this course. All default to `true`. See below. |
| `theme` | no | `{ "accent": "#4F46E5", "css": "theme.css" }`. See below. |
| `support` | no | A folder of helper files exercise code can import (e.g. a fake API client for offline tests). |
| `sections` | yes | The course content, in order. |

### `features`: what the interface shows

| Key | Turns on or off |
|---|---|
| `notes` | The notes drawer (Apple Notes-style), per lesson and free-standing. |
| `timer` | The Pomodoro focus timer in the top bar. |
| `focusMode` | Focus mode (the F key or the ⛶ button): puts the browser in full screen. |
| `studyStats` | The dashboard's Today panel: study time, daily goal, streak and week chart. |
| `review` | The review queue: missed quiz questions come back on later days. |
| `browser` | The built-in link viewer: links open in a panel inside the course instead of a new tab. |

Example: a reading-only course with no timer or review:

```json
"features": { "timer": false, "review": false }
```

### `theme`: how it looks

- `accent`: the course's colour for buttons, progress bars, highlights and the like.
- `css`: an **add-on stylesheet** inside the pack. It loads after the platform's styles, so it can restyle anything. The simplest way is to override the design tokens:

```css
:root {
  --accent: #0F766E;
  --radius: 16px;  --radius-s: 10px;
  --font-body: "Inter", system-ui, sans-serif;
  --bg: #F7F7F5;  --surface: #FFFFFF;  --ink: #1A1A1A;  --muted: #6B6B6B;  --line: #E5E5E5;
}
```

## Sections

| Field | What it does |
|---|---|
| `id`, `title` | Required. |
| `summary` | One or two sentences on the dashboard. |
| `status` | `"ready"` (default) or `"coming-soon"`: shown in the outline but locked, so you can publish a course while it grows. |
| `lessons` | The lessons, in order. |
| `project` | Optional section project. |

## Lessons

| Field | What it does |
|---|---|
| `id`, `title`, `body` | Required. `body` is Markdown: headings, code blocks with highlighting, tables, `> blockquotes` for tips. If it starts with `# Title`, that line is hidden because the page already shows the title. |
| `duration` | Free text, e.g. `"45 min"`. |
| `videos` | Embedded players. `{ "youtube": "VIDEO_ID", "title": "...", "start": 90 }` or `{ "playlist": "PLAYLIST_ID", "title": "..." }`. Several videos show as tabs. |
| `resources` | "Go deeper" links that open in a new tab. |
| `practice` | Code exercises and quizzes. |

## Practice

### Code exercises

```json
{ "id": "add-two", "type": "code", "title": "Add two numbers",
  "language": "typescript",
  "prompt":   { "file": "practice/add-two/prompt.md" },
  "starter":  { "file": "practice/add-two/starter.ts" },
  "tests":    { "file": "practice/add-two/tests.ts" },
  "solution": { "file": "practice/add-two/solution.ts" },
  "needs_api_key": false }
```

- **Run** executes the learner's code and shows its output. **Check** runs the hidden tests and reports each one as passed or failed. **Show solution** reveals `solution`.
- Learner code is saved as `solution.<ext>`, and tests import from it.
- **Python** tests are functions named `test_*` that use `assert`:
  ```python
  from solution import add

  def test_adds_small_numbers():
      assert add(2, 3) == 5, "2 + 3 should be 5"
  ```
- **JavaScript/TypeScript** tests run on Node 24. TypeScript runs directly; use only erasable syntax, so no `enum` or `namespace`. Call the platform's global `test()` and Node's `assert`:
  ```ts
  import assert from "node:assert/strict";
  import { add } from "./solution.ts";

  test("adds small numbers", () => {
    assert.equal(add(2, 3), 5);
  });
  ```
  Don't import `test` from `node:test`. Its fake timers (`import { mock } from "node:test"`) are fine to use.
- **Test names are shown to learners.** Make them read like sentences.
- `needs_api_key: true` shows a badge saying Run calls a paid API. Check should always be offline: use a fake from `support/`.

### Quizzes

```json
{ "id": "first-quiz", "type": "quiz",
  "question": "Which file describes a course?",
  "options": ["index.html", "course.json", "server.py"],
  "answer": 1,
  "explanation": "Everything about a course lives in its pack's course.json." }
```

`answer` is the index of the correct option. If `review` is on, a quiz the learner gets wrong joins their review queue.

## Projects

```json
"project": { "id": "basics-project", "title": "Build a CLI tool",
  "brief": { "file": "projects/basics.md" },
  "checklist": ["Parses arguments", "Has tests", "README with a demo GIF"],
  "links": true }
```

The checklist items are ticked off by the learner. `links: true` adds fields for the project's GitHub repo and live URL.

## Rules the validator enforces

- Ids are unique across the whole course and match `^[a-z0-9][a-z0-9-]{0,63}$`.
- File references stay inside the pack.
- Quiz `answer` is a valid option index. `language` is a supported language. `features` keys are known, and their values are true/false. `theme.accent` is a `#RRGGBB` colour. `theme.css` exists.
- **Every code exercise's `solution` passes its own `tests`.** A pack whose answers fail its own tests is broken, and `validate` says which ones fail.

## What learners' data looks like (not part of the pack)

Progress, notes and saved code live in `learner-data/<course-id>/`, never in the pack. That means a pack can be shared, sold or updated without touching anyone's work, and updating a pack keeps the learner's progress as long as ids don't change. **Renaming an id resets progress for that item**, so treat published ids as permanent.
