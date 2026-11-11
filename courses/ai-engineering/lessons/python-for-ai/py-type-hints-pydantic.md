# Type hints and Pydantic

## Why this matters

An LLM returns text. To use its answer in a program, you need it as structured data with known fields and types, and you need to reject it when it doesn't fit. Pydantic is how Python AI code does that: you describe the shape once as a class, and Pydantic validates incoming data against it **and** generates the JSON Schema you send to the model for structured output and tool definitions. The Claude SDK, FastAPI and most agent frameworks are built on it. Type hints are the language Pydantic reads, so we start there.

## Type hints

A type hint says what type a variable, parameter or return value is meant to be:

```python
def greet(name: str, times: int = 1) -> str:
    return " ".join([f"Hello {name}!"] * times)

model: str = "claude-haiku-5-5"
```

Python itself **does not enforce hints at runtime**. `greet(42)` still runs. Hints are for:

- **Your editor:** autocomplete and inline errors as you type.
- **Type checkers** like mypy or pyright, which find bugs before you run anything.
- **Libraries** like Pydantic and FastAPI, which read hints at runtime and act on them.
- **Readers**, including you in three weeks.

### Collections and generics

Built-in collection types take the type of their contents in square brackets:

```python
names: list[str] = ["Ada", "Grace"]
scores: dict[str, float] = {"Ada": 0.9}
point: tuple[float, float] = (1.0, 2.0)        # fixed length: two floats
history: tuple[str, ...] = ("a", "b", "c")      # any length, all str
unique: set[int] = {1, 2, 3}
```

For parameters, the abstract types from `collections.abc` are often better, because they accept more:

```python
from collections.abc import Iterable, Mapping, Callable

def total(xs: Iterable[float]) -> float:     # list, tuple, generator: anything you can loop over
    return sum(xs)

def apply(f: Callable[[str], int], s: str) -> int:   # a function taking str, returning int
    return f(s)

print(total((1.5, 2.5)), apply(len, "hello"))  # 4.0 5
```

A **generic** function works for any type but keeps the relationship between input and output. Python 3.12 has a short syntax with square brackets after the name:

```python
def first[T](items: list[T]) -> T:
    return items[0]

x = first([1, 2, 3])        # the checker knows x is an int
y = first(["a", "b"])       # ...and y is a str
```

### Unions, Optional and None

`X | Y` means "either X or Y". A value that may be missing is `X | None`:

```python
def find_user(user_id: int) -> dict | None:
    users = {1: {"name": "Ada"}}
    return users.get(user_id)

user = find_user(2)
if user is not None:          # a checker makes you handle the None case
    print(user["name"])
```

You'll see `Optional[X]` from `typing` in older code; it means exactly `X | None`. Prefer the `|` form in new code.

### Literal

`Literal` restricts a value to specific constants. It's perfect for roles, modes and categories:

```python
from typing import Literal

Role = Literal["user", "assistant"]          # a type alias

def message(role: Role, content: str) -> dict:
    return {"role": role, "content": content}

message("user", "Hi")        # fine
message("system", "Hi")      # runs, but your checker flags it
```

### TypedDict

Sometimes you must work with plain dicts (for example the message dicts the Claude SDK accepts) but still want the keys typed. `TypedDict` describes a dict's keys and value types without changing anything at runtime:

```python
from typing import TypedDict

class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str

msg: Message = {"role": "user", "content": "Hi"}   # still a normal dict
```

The SDK's own type definitions are written this way, which is why your editor can autocomplete `messages=[{"role": ...}]`.

## Pydantic: hints that are enforced

Pydantic turns a class with type hints into a validator. Subclass `BaseModel` and declare fields:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str | None = None      # optional, defaults to None

u = User(name="Ada", age="36")    # "36" is converted to 36
print(u)                          # name='Ada' age=36 email=None
print(u.age + 1)                  # 37
```

Note what happened: `age="36"` was **coerced** to the integer 36, because it unambiguously represents one. Something that can't be converted is rejected with a clear error instead of producing a broken object. That's the main difference from a dataclass.

### Field constraints

`Field(...)` adds rules beyond the type, plus a description and default:

```python
from typing import Literal
from pydantic import BaseModel, Field

class Ticket(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    priority: Literal["low", "medium", "high"] = "medium"
    estimate_hours: float = Field(gt=0, le=40, description="Hours of work, at most one week")
    tags: list[str] = Field(default_factory=list)
```

Common constraints: `gt`, `ge`, `lt`, `le` for numbers; `min_length`, `max_length` for strings and lists; `pattern` for a regular expression on strings. `alias` maps a field to a differently named key in the input, for example `user_id: int = Field(alias="userId")` for camelCase JSON.

### Validation errors

Invalid data raises `pydantic.ValidationError`, which lists **every** problem, not just the first:

```python
from pydantic import ValidationError

try:
    Ticket(title="", priority="urgent", estimate_hours="abc")
except ValidationError as e:
    print(e)
```

```text
3 validation errors for Ticket
title
  String should have at least 1 character [type=string_too_short, input_value='', input_type=str]
priority
  Input should be 'low', 'medium' or 'high' [type=literal_error, input_value='urgent', input_type=str]
estimate_hours
  Input should be a valid number, unable to parse string as a number [type=float_parsing, ...]
```

For programmatic use, `e.errors()` returns a list of dicts; each has `"loc"` (a tuple with the field path), `"msg"` and `"type"`:

```python
for err in e.errors():
    print(err["loc"], err["msg"])
# ('title',) String should have at least 1 character
# ...
```

> **Note:** `ValidationError` is a subclass of `ValueError`. If you also catch `ValueError` nearby (for example from `json.loads`), catch `ValidationError` first or keep the two steps in separate `try` blocks.

### `model_validate`, `model_dump`, and JSON

Data from the outside world usually arrives as a dict or a JSON string. Pydantic has a method for each direction:

```python
data = {"title": "Fix login", "estimate_hours": 2.5}
t = Ticket.model_validate(data)                 # dict -> model (validated)
t2 = Ticket.model_validate_json('{"title": "Fix", "estimate_hours": "2.5"}')   # JSON text -> model

print(t.model_dump())        # model -> dict
# {'title': 'Fix login', 'priority': 'medium', 'estimate_hours': 2.5, 'tags': []}
print(t.model_dump_json())   # model -> JSON string
# {"title":"Fix login","priority":"medium","estimate_hours":2.5,"tags":[]}
```

`model_validate` is the one you'll use most: parse with `json.loads` or let httpx parse the response, then validate the dict. Models nest naturally; a field typed `list[Ticket]` validates every item.

```python
class Backlog(BaseModel):
    team: str
    tickets: list[Ticket]

b = Backlog.model_validate({"team": "AI", "tickets": [{"title": "Eval set", "estimate_hours": 8}]})
print(b.tickets[0].priority)   # medium
```

### `model_json_schema`: the bridge to LLMs

Every model can describe itself as a **JSON Schema**, the standard format for "what valid JSON looks like":

```python
import json
print(json.dumps(Ticket.model_json_schema(), indent=2))
```

```json
{
  "properties": {
    "title": {"maxLength": 100, "minLength": 1, "title": "Title", "type": "string"},
    "priority": {"default": "medium", "enum": ["low", "medium", "high"], "title": "Priority", "type": "string"},
    "estimate_hours": {"description": "Hours of work, at most one week", "exclusiveMinimum": 0,
                       "maximum": 40, "title": "Estimate Hours", "type": "number"},
    "tags": {"items": {"type": "string"}, "title": "Tags", "type": "array"}
  },
  "required": ["title", "estimate_hours"],
  "title": "Ticket",
  "type": "object"
}
```

This is exactly what LLM APIs consume:

- **Structured output.** You can ask Claude to answer in a given shape. The SDK accepts a Pydantic model directly, sends its schema to the API, and validates the reply for you:

  ```python
  response = client.messages.parse(
      model="claude-opus-5-5", max_tokens=16000,
      messages=[{"role": "user", "content": "Make a ticket: the login page is slow"}],
      output_format=Ticket,
  )
  ticket = response.parsed_output      # a validated Ticket instance
  ```

- **Tools.** When you give the model a tool, you describe its arguments with a JSON Schema in `input_schema`. Generating it from a model keeps the schema and your Python code in sync:

  ```python
  class SearchInput(BaseModel):
      query: str = Field(description="What to search for")
      limit: int = Field(default=5, ge=1, le=20)

  search_tool = {
      "name": "search_docs",
      "description": "Search the documentation.",
      "input_schema": SearchInput.model_json_schema(),
  }
  # Later, when the model calls the tool:
  # args = SearchInput.model_validate(tool_use_block.input)
  ```

`Field(description=...)` ends up in the schema, and the model reads it, so good descriptions directly improve how well the model fills the fields. You'll use both features in the next section; this lesson's second exercise builds a tool definition.

> **Try it:** Add a `due: str | None = None` field to `Ticket` and print the schema again. Notice it's not in `required`, and its type is `anyOf` string or null.

### Dataclass or Pydantic?

Use a **dataclass** for data your own code creates and trusts: internal records, results you pass between functions. Use **Pydantic** at the boundaries, wherever data comes from outside: HTTP responses, request bodies, config files, user input and every LLM output. Validation has a cost, so you pay it where untrusted data enters.

## Common mistakes

- **Expecting plain type hints to be enforced.** `def f(x: int)` accepts a string. Only tools like Pydantic enforce hints.
- **Using `model.dict()` / `parse_obj()`.** Those are Pydantic v1 names. In v2 they're `model_dump()` and `model_validate()`. Old tutorials use v1; check which version you're reading.
- **Catching `ValueError` before `ValidationError`.** The broader handler wins and you report the wrong problem.
- **Mutable defaults.** Prefer `Field(default_factory=list)` for list fields; it's the explicit, always-safe form.
- **Forgetting descriptions on tool and output schemas.** The model only knows what the schema tells it. A field called `q` with no description gets worse input than `query` described as "keywords to search for".
- **Validating too late.** Validate as soon as data enters your program, then pass the model around. Code after the boundary can trust it.

## Recap

- Type hints describe types (`list[str]`, `dict[str, int]`, `X | None`, `Literal[...]`, `TypedDict`, generics with `def f[T]`); Python doesn't enforce them, tools do.
- Pydantic `BaseModel` enforces hints at runtime, coerces compatible values, and raises a `ValidationError` listing every problem.
- `Field(...)` adds constraints (`ge`, `le`, `min_length`, `pattern`), descriptions, defaults and aliases.
- `model_validate` (dict → model), `model_validate_json` (JSON → model), `model_dump` / `model_dump_json` (model → dict / JSON).
- `model_json_schema()` produces the JSON Schema that LLM structured output and tool definitions use.
