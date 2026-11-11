# Modern Python essentials

## Why this matters

AI code is full of small data wrangling: building prompts from variables, filtering lists of documents, turning API responses into objects, reading config files, and failing clearly when something is wrong. The features in this lesson are the ones you'll type every day for that work. If they're automatic, your attention stays on the actual problem.

## f-strings

An f-string is a string literal prefixed with `f`; anything in `{}` is evaluated and inserted. This is how you'll build most prompts.

```python
name, n_docs = "Ada", 3
print(f"Hello {name}, I found {n_docs} documents.")
# Hello Ada, I found 3 documents.

price = 0.0123456
print(f"Cost: ${price:.4f}")       # Cost: $0.0123   (format spec after the colon)
print(f"{1234567:,}")              # 1,234,567
print(f"{name!r}")                 # 'Ada'           (!r uses repr(): shows quotes)
print(f"{n_docs=}")                # n_docs=3        (handy for debugging)
```

Multi-line prompts use triple-quoted f-strings:

```python
question = "What is RAG?"
context = "RAG means retrieval-augmented generation."
prompt = f"""Answer using only the context.

<context>
{context}
</context>

Question: {question}"""
print(prompt)
```

> **Note:** To put a literal brace in an f-string, double it: `f"{{not a variable}}"`. You'll hit this when an f-string contains JSON.

## Comprehensions

A comprehension builds a list, dict or set from an iterable in one expression. The pattern is `[expression for item in iterable if condition]`.

```python
scores = [0.91, 0.42, 0.77, 0.13]
good = [s for s in scores if s > 0.5]               # [0.91, 0.77]
rounded = [round(s, 1) for s in scores]             # [0.9, 0.4, 0.8, 0.1]

docs = [{"id": "a", "text": "cats"}, {"id": "b", "text": "dogs"}]
by_id = {d["id"]: d["text"] for d in docs}          # {'a': 'cats', 'b': 'dogs'}
lengths = {len(d["text"]) for d in docs}            # {4}   (a set: unique values)
```

A comprehension is right when it's short and clearly "transform and/or filter". If you need several statements, `try`/`except`, or the line gets hard to read, write a normal `for` loop instead. Readability wins.

## Unpacking

Python can assign several names at once from any iterable.

```python
role, content = ("user", "Hi")
first, *rest = [1, 2, 3, 4]       # first=1, rest=[2, 3, 4]
*_, last = [1, 2, 3, 4]           # last=4  (_ means "I don't care")

for i, doc in enumerate(["a", "b"], start=1):
    print(i, doc)                  # 1 a / 2 b

for question, answer in zip(["2+2?", "Capital of France?"], ["4", "Paris"]):
    print(question, "->", answer)
```

`*` and `**` also unpack into function calls and literals, which is how you merge settings:

```python
defaults = {"model": "claude-haiku-5-5", "max_tokens": 1024}
overrides = {"max_tokens": 4000}
settings = {**defaults, **overrides}   # later keys win
print(settings)  # {'model': 'claude-haiku-5-5', 'max_tokens': 4000}

def call(model, max_tokens):
    return f"{model} with {max_tokens} tokens"
print(call(**settings))
```

## Dataclasses

When you have a bundle of related fields, a plain dict is easy to misspell (`msg["contnet"]` fails only at runtime). A **dataclass** gives you a small class with named, typed fields and a free `__init__`, `__repr__` and `__eq__`.

```python
from dataclasses import dataclass, field

@dataclass
class Document:
    id: str
    text: str
    score: float = 0.0
    tags: list[str] = field(default_factory=list)   # new list per instance

d = Document("a", "cats are great")
print(d)                 # Document(id='a', text='cats are great', score=0.0, tags=[])
print(d.text.upper())    # CATS ARE GREAT
print(d == Document("a", "cats are great"))   # True: compares field by field
```

Two options worth knowing: `@dataclass(frozen=True)` makes instances immutable (and hashable, so usable as dict keys), and `@dataclass(slots=True)` uses less memory.

Dataclasses do **not** check types. `Document(id=1, text=None)` happily creates a broken object. When data comes from outside your program (JSON, user input, an LLM), you want validation; that's Pydantic, in the next lesson.

> **Note:** Never write `tags: list[str] = []` in a dataclass; Python raises a `ValueError` because all instances would share one list. Use `field(default_factory=list)`.

## Exceptions

Errors in Python are exceptions. You raise them when something is wrong, and catch them where you can do something useful about it.

```python
def parse_age(text: str) -> int:
    age = int(text)                       # raises ValueError for "abc"
    if age < 0:
        raise ValueError(f"age must be >= 0, got {age}")
    return age

try:
    parse_age("abc")
except ValueError as e:
    print("bad input:", e)
else:
    print("only runs if nothing was raised")
finally:
    print("always runs: close files, release locks, log timing")
```

Rules of thumb:

- **Catch specific exceptions.** `except ValueError:` says what you expect. A bare `except:` or `except Exception:` also swallows bugs like `NameError` from a typo.
- **Catch where you can act.** If you can't fix it, retry it, or turn it into a clearer error, let it propagate.
- **Don't silence errors.** `except Exception: pass` turns a crash you could debug into wrong output you can't.

### Custom exceptions

Libraries define their own exception classes so callers can catch "anything from this library" precisely. The Claude SDK has `anthropic.RateLimitError`, `anthropic.BadRequestError` and so on. Defining one is a single line:

```python
class ConfigError(Exception):
    """Raised when the config file is missing or invalid."""

import json

def parse_config(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise ConfigError("config is not valid JSON") from err
```

`raise ... from err` chains the original error, so the traceback shows both: your clear message and the low-level cause. Callers now write `except ConfigError:` without knowing that JSON was involved.

## Modules and `if __name__ == "__main__"`

Every `.py` file is a module. `import tools` runs `tools.py` once and gives you its names as `tools.something`; `from tools import something` imports one name directly.

When Python runs a file directly (`python tools.py`), it sets that module's `__name__` to `"__main__"`. When the file is imported, `__name__` is the module's name (`"tools"`). That lets one file be both a reusable module and a runnable script:

```python
# tools.py
def word_count(text: str) -> int:
    return len(text.split())

if __name__ == "__main__":
    # Only runs with `python tools.py`, not on `import tools`.
    print(word_count("one two three"))
```

Without the guard, importing `tools` from another file (or from a test) would run the demo code too. That's why the starter files in this course put their demos under this guard: Check imports your file, and the demo stays quiet.

## `pathlib`

`pathlib.Path` is the modern way to work with file paths. It joins paths with `/`, works on every OS, and has methods for the common file operations.

```python
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)     # create if missing

notes = data_dir / "notes.txt"                  # data/notes.txt
notes.write_text("first line\nsecond line\n", encoding="utf-8")
print(notes.read_text(encoding="utf-8").splitlines())   # ['first line', 'second line']
print(notes.exists(), notes.suffix, notes.stem)         # True .txt notes

for p in sorted(data_dir.glob("*.txt")):        # every .txt file in data/
    print(p.name)
```

For large files, don't `read_text()` the whole thing; open it and loop over lines (you'll see why in the generators lesson):

```python
with notes.open(encoding="utf-8") as f:
    for line in f:
        print(line.rstrip())
```

`Path(__file__).parent` is the folder containing the current script, useful for finding files next to your code regardless of where it was launched from.

## The `json` module

JSON is the language of web APIs and LLM structured output. The `json` module converts between JSON text and Python objects: objects ↔ `dict`, arrays ↔ `list`, strings ↔ `str`, numbers ↔ `int`/`float`, `true`/`false` ↔ `True`/`False`, `null` ↔ `None`.

```python
import json

text = '{"model": "claude-haiku-5-5", "tags": ["fast"], "stream": false, "seed": null}'
data = json.loads(text)                 # str -> Python
print(data["tags"][0], data["stream"])  # fast False

out = json.dumps(data, indent=2)        # Python -> str (pretty-printed)
print(out)

from pathlib import Path
Path("config.json").write_text(json.dumps(data), encoding="utf-8")
loaded = json.loads(Path("config.json").read_text(encoding="utf-8"))
print(loaded == data)                   # True
```

`json.load(f)` and `json.dump(obj, f)` (without the `s`) work on open files instead of strings. Invalid JSON raises `json.JSONDecodeError` (a subclass of `ValueError`), and Python objects JSON doesn't know (sets, dataclasses, datetimes) make `dumps` raise `TypeError`. Convert them first, for example with `dataclasses.asdict(obj)`.

> **Try it:** Run `json.loads("{'a': 1}")`. JSON requires double quotes, so this fails. LLMs occasionally produce near-JSON like this, which is one reason structured output features exist.

## Common mistakes

- **Mutable default arguments.** `def add(item, items=[])` shares one list across calls. Use `items=None` and create the list inside.
- **Catching too broadly.** `except Exception:` around a whole function hides typos. Wrap only the line that can fail, and name the exception.
- **Forgetting `encoding="utf-8"`.** Some systems default to another encoding, and text with accents or emoji then breaks. Be explicit when reading and writing text.
- **Comprehensions that do too much.** If it needs a comment to explain, make it a loop.
- **Demo code without the `__main__` guard.** It runs on every import, including from tests.
- **`json.dumps` on objects it can't handle.** Convert dataclasses with `asdict()` first (Pydantic models have their own `model_dump()`).

## Recap

- f-strings build text (and prompts): `f"{value:.2f}"`, `f"{name!r}"`, `f"{x=}"`.
- Comprehensions transform and filter in one readable expression; use loops when it stops being readable.
- Unpacking (`a, *rest = ...`, `{**a, **b}`, `f(**kwargs)`) moves data around cleanly.
- Dataclasses give named, typed fields with no validation.
- Raise specific exceptions, catch them where you can act, define your own, and chain with `from err`.
- `if __name__ == "__main__":` keeps script code from running on import.
- `pathlib.Path` for paths and files; `json.loads`/`json.dumps` for JSON.
