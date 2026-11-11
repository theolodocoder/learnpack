# Welcome and setup

## Why this matters

AI engineering is mostly ordinary software engineering with a model call in the middle. The code around that call (reading config, validating data, calling HTTP APIs, running things concurrently, handling failures, testing) decides whether your product works. This first week makes sure your Python is sharp enough that none of that slows you down, and gets your machine ready so that the rest of the course is just "open the lesson and go".

## How to study here

Every lesson follows the same loop. Stick to it; it is designed so you actually keep what you learn.

1. **Read.** The written lesson is the main teaching. It explains the idea, shows short runnable examples, then lists common mistakes. Read it with the code editor open and type the examples yourself instead of only reading them. Typing catches misunderstandings that reading hides.
2. **Watch.** Most lessons have a video underneath. It's a companion: a second explanation from a different angle. If the written lesson already clicked, you can skim the video or skip it.
3. **Practise.** Each lesson ends with code exercises and a quiz question or two. The exercises are where learning happens. Don't open the reference solution until you've had a real attempt (at least 15 minutes of being stuck).
4. **Notes.** Write a few lines in your own words: what the idea is, one example, one gotcha. Short notes you wrote beat long notes you copied.
5. **Mark done.** Tick the lesson when you can do the exercises without help. That's the bar, not "I read it".

A good rhythm is one or two lessons a day, with the section project at the end of the week. If a lesson takes longer, that's fine; skipping practice to keep pace is not.

## Setting up your machine

You need three things: Python, a virtual environment with the course packages, and (later) an API key.

### Python and uv

Check your Python version in a terminal:

```bash
python3 --version
# Python 3.12 or newer is required
```

We use [uv](https://docs.astral.sh/uv/) to manage environments and packages. It does the job of `python -m venv` and `pip`, much faster. Install it once:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or, with Homebrew
brew install uv
```

### The project virtual environment

A **virtual environment** ("venv") is a folder containing its own Python interpreter and its own installed packages. Every project gets one, so project A can use `pydantic` 2 while an old project B uses `pydantic` 1, without either breaking the other. Never install project packages into your system Python.

From the root of this repository, run:

```bash
uv venv
uv pip install -r requirements.txt
```

The first command creates `.venv/` in the repo root. The second installs the packages listed in `requirements.txt`: `anthropic` (the Claude SDK), `pydantic`, `httpx`, `numpy` and `python-dotenv`. The code editor in each lesson uses this environment automatically when it exists.

To use the venv in your own terminal, activate it:

```bash
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
python -c "import pydantic; print(pydantic.VERSION)"
```

When the venv is active, `python` and `pip` refer to the venv's copies. `deactivate` turns it off. You can also skip activation and call the interpreter directly with `.venv/bin/python script.py`, or use `uv run script.py`, which finds the venv for you.

> **Note:** `requirements.txt` is the list of what your project needs. When you add a package to a real project, add it to that file (or use `uv add` in a uv-managed project) so the next person, or the server you deploy to, can rebuild the same environment.

### API keys and `.env`

From the second section on, you'll call Claude. That needs an API key from the Anthropic Console. An API key is a password: anyone who has it can spend your money. So it never goes in your code and never gets committed to Git.

The standard place for keys during development is a `.env` file in the repo root:

```bash
# .env  (never commit this file)
ANTHROPIC_API_KEY=sk-ant-...
```

Make sure `.env` is listed in `.gitignore`. Then, in your own scripts, load it with `python-dotenv`:

```python
import os
from dotenv import load_dotenv

load_dotenv()                      # reads .env into os.environ (doesn't overwrite existing vars)
key = os.environ.get("ANTHROPIC_API_KEY")
print("key loaded" if key else "no key found")
```

`load_dotenv()` looks for a `.env` file in the current folder and its parents, and copies each `NAME=value` line into the process environment. Code then reads settings with `os.environ`. That's the same mechanism production servers use, except there the variables are set by the hosting platform instead of a file. Your code doesn't need to know the difference.

The Claude SDK reads `ANTHROPIC_API_KEY` from the environment by itself, so `anthropic.Anthropic()` just works once the variable is set.

You don't need a key this week. Every exercise here runs offline.

## Run and Check

Every code exercise has two buttons.

- **Run** executes your file as a script with the course's Python, exactly like `python solution.py`. Whatever you `print` shows up below the editor. Use it to experiment. Most starter files end with an `if __name__ == "__main__":` block that calls your function on an example, so you can see what it returns. If you have a `.env` with an API key, Run passes it to your code.
- **Check** runs the hidden tests against your code. Each test is a small function that calls your code with some input and asserts on the result. You'll see a list of test names (for example "rejects negative age") with a pass or fail mark, and the failure message tells you what was expected and what you returned. Check never calls a real API and never costs money. Tests for API-calling exercises use fakes.

Here's what a test looks like, so the output isn't mysterious:

```python
from solution import word_counts

def test_ignores_case():
    got = word_counts("Python python PYTHON")
    want = {"python": 3}
    assert got == want, f"expected {want!r}, got {got!r}"
```

Your code is saved as `solution.py`, the test imports your function from it, calls it, and compares. That's the whole trick, and in the last lesson of this week you'll write tests like this yourself.

A productive loop is: write a bit, **Run** to see what it does, fix, then **Check**. Read failure messages carefully; they usually tell you exactly what's wrong.

> **Try it:** In the warm-up exercise, press Check before writing anything. Read the failing tests' names and messages: they describe the spec.

## A quick Python warm-up

If your Python is rusty, here's the minimum you need for the warm-up exercise. Strings have handy methods:

```python
s = "  Hello, World!  "
print(s.strip())          # 'Hello, World!'      (removes whitespace at both ends)
print(s.lower())          # '  hello, world!  '
print("Wow!!".strip("!")) # 'Wow'                 (removes these characters at both ends)
print("a b  c".split())   # ['a', 'b', 'c']       (splits on any run of whitespace)
```

Dictionaries map keys to values. `dict.get(key, default)` returns a default when the key is missing, which makes counting easy:

```python
counts: dict[str, int] = {}
for word in ["a", "b", "a"]:
    counts[word] = counts.get(word, 0) + 1
print(counts)  # {'a': 2, 'b': 1}
```

The standard library also has `collections.Counter`, which does exactly this:

```python
from collections import Counter
print(Counter(["a", "b", "a"]))  # Counter({'a': 2, 'b': 1})
```

Either approach is fine for the exercise.

## What this week covers

The rest of the week rebuilds your Python toward one goal: by Friday you'll write an async client that fetches several JSON endpoints at once, validates every response with Pydantic, survives failures, and writes a report. That small project uses every lesson:

- **Modern Python essentials:** the everyday syntax and standard-library modules you'll use in every file.
- **Type hints and Pydantic:** how you describe data, and how LLM structured output and tool schemas are defined.
- **Iterators and generators:** how streamed LLM responses are consumed piece by piece.
- **Decorators and context managers:** retries, timers, and the `with` blocks you'll see in every SDK.
- **Async Python:** running many slow network calls at the same time.
- **HTTP and JSON with httpx:** talking to any web API, and testing that code without a network.
- **Testing:** proving your code works, then the project.

## Common mistakes

- **Installing packages globally.** `pip install pydantic` without an active venv puts it in your system Python, and then "it works on my machine" but not in the project. Always create the venv first and use `uv pip install` (or the venv's `pip`).
- **Committing `.env`.** Check `.gitignore` before your first commit. If a key ever lands on GitHub, revoke it in the console immediately; bots scan public repos for keys within minutes.
- **Hard-coding a key "just for a test".** It always ends up committed. Read it from the environment from day one.
- **Reading the solution too early.** Being stuck for a while is the part that teaches you. Re-read the lesson section, print intermediate values with Run, then look.
- **Ignoring the failure message.** "expected {'the': 2}, got {'The': 1, 'the': 1}" tells you exactly that you forgot to lowercase.

## Recap

- Study loop: read, watch, practise, write notes, mark done when you can do the exercises unaided.
- Create the project environment once from the repo root with `uv venv && uv pip install -r requirements.txt`.
- Keys live in `.env` (git-ignored); `load_dotenv()` loads them into `os.environ`, and the Claude SDK reads `ANTHROPIC_API_KEY` from there.
- **Run** executes your file; **Check** runs offline tests that import your code from `solution.py` and assert on the results.
