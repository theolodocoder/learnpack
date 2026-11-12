# Getting started

This guide takes you from download to your first finished exercise, in about five minutes.

## 1. Install what it needs

| What | Why | Check you have it |
|---|---|---|
| **Python 3.10 or newer** | Runs the app and the Python exercises | `python3 --version` (Windows: `python --version`) |
| **Node.js 24 or newer** | Only for courses with JavaScript/TypeScript exercises (not needed for AI Engineering) | `node --version` |
| **A modern browser** | Chrome, Edge, Firefox, Safari | — |
| **Internet** | For embedded videos and fonts. Lessons, exercises and notes work offline | — |

Install Python from [python.org/downloads](https://www.python.org/downloads/). On Windows, tick **"Add python.exe to PATH"** in the installer. Install Node.js from [nodejs.org](https://nodejs.org/) (the LTS version).

[`uv`](https://docs.astral.sh/uv/) is optional. If it's installed, the first-time setup is faster.

## 2. Download LearnPack

On the [GitHub page](https://github.com/theolodocoder/learnpack), click **Code → Download ZIP** and unzip it somewhere you'll find again, such as Documents.

Or with git:

```bash
git clone https://github.com/theolodocoder/learnpack.git
cd learnpack
```

## 3. Start it

### Mac

Double-click **`Start Learning.command`**.

The first time, macOS may block it as "from an unidentified developer". Right-click the file → **Open** → **Open**. macOS remembers your choice.

If it opens in a text editor instead of running, open Terminal in the folder and run this once:

```bash
chmod +x "Start Learning.command"
```

### Windows

Double-click **`Start Learning.bat`**. If Windows SmartScreen appears, click **More info** → **Run anyway**.

### Linux, or any terminal

`./"Start Learning.command"` works on Linux too. To do it by hand:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once: packages the exercises use
python3 server.py
```

### What happens

- **First launch only:** a `.venv` folder is created with the packages the exercises use. This takes about a minute.
- **Your browser opens** at **http://localhost:8000**.
- **A small terminal window stays open.** That window *is* the app: keep it open while you study, and close it to stop.
- **Double-clicking again** while it's running just opens the browser again.

## 4. Find your way around

```
┌───────────────────────────────────────────────────────────────────────┐
│ ☰  AI Engineering ▾           ▬▬▬ 12% done   ● 25:00  ⛶  Notes  ◐   │  ← top bar
├──────────────┬────────────────────────────────────────────────────────┤
│ ↻ Review  2  │  Lesson title                                          │
│ ▾ Section 1  │  [ video ]                                             │
│   ○ Lesson   │  Written lesson…                                       │
│   ✓ Lesson   │  Go deeper (links)                                     │
│   ☐ Project  │  Practice: editor  [Check] [Run]                       │
│ ▸ Section 2  │  [ Mark as done ]                    Previous · Next   │
└──────────────┴────────────────────────────────────────────────────────┘
```

| Control | What it does |
|---|---|
| **☰** | Hide or show the course outline |
| **Course title ▾** | Switch between installed courses |
| **● 25:00** | Focus timer (Pomodoro): click to start, pause or change lengths |
| **⛶** | Focus mode: full screen. Press **F** to toggle, **Esc** to leave. Use **☰** to hide the outline too |
| **Notes** | Your notes for this lesson. **‹ Notes** lists all notes, with search |
| **◐** | Switch between system, light and dark mode |
| **↻ Review** | Quiz questions you missed, due for another try |

## 5. Do your first exercise

1. Open the first lesson of a course and scroll to **Practice**.
2. Write code in the editor. It autosaves.
3. **Run** (⌘/Ctrl+Enter) runs your code and shows its output.
4. **Check** (Shift+Enter) runs hidden tests. Each test shows ✓ or ✗ with a short message pointing at the line.
5. Stuck? **Show solution** reveals the reference answer. **Reset** brings back the starter code.
6. When you're done with the lesson, click **Mark as done**.

Your code, notes and progress are saved as files in `learner-data/` in the LearnPack folder. Clearing your browser loses nothing. Back that folder up if you want to move to a new computer.

## 6. Optional: an API key for the AI Engineering course

Some AI exercises call Claude. **Check** never needs a key, because it uses a built-in fake. To see real model output when you click **Run**:

1. Get a key at [console.anthropic.com](https://console.anthropic.com/).
2. In the LearnPack folder, copy `.env.example` to `.env` and paste in your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Restart the app.

Exercises marked **Uses API key on Run** cost a small amount per run. `.env` is never uploaded anywhere and is excluded from git.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Python 3.10 or newer is needed" | Install Python from python.org. On Windows, tick **Add python.exe to PATH**, then try again |
| "Port 8000 is busy with something else" | Another program uses that port. Run `python3 server.py --port 8001` and open http://localhost:8001 |
| Browser didn't open | Open http://localhost:8000 yourself |
| A Python exercise fails with `ModuleNotFoundError` | The first-run setup didn't finish. Delete the `.venv` folder and start again, or run `python3 -m venv .venv` then `.venv/bin/pip install -r requirements.txt` (Windows: `.venv\Scripts\pip install -r requirements.txt`) |
| JavaScript/TypeScript exercises say Node.js is needed | Install Node.js 24+ from nodejs.org and restart the app |
| "Save failed" in notes or the editor | The app window was closed. Start it again; your text stays on the page until you reload |
| Videos don't load | Videos need internet. Everything else works offline |
| A course doesn't appear | Its `course.json` has a problem. Run `python3 server.py validate courses/<folder>` to see what |

Still stuck? [Open an issue](https://github.com/theolodocoder/learnpack/issues).
