# Validate user records with Pydantic

You've been handed a batch of user records from a sign-up form. Some are bad. Validate them all, keep the good ones, and report the bad ones without stopping.

Write a Pydantic model and a function:

```python
class User(BaseModel):
    name: str        # 1 to 50 characters
    age: int         # 0 to 150 inclusive
    email: str       # must match the pattern r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    tags: list[str]  # optional, defaults to an empty list

def parse_users(rows: list[dict]) -> tuple[list[User], list[str]]:
```

Use `Field(...)` for the constraints (`min_length`, `max_length`, `ge`, `le`, `pattern`, `default_factory`).

`parse_users` validates each row with `User.model_validate(row)`.

- Valid rows go into the first list, in order.
- For each invalid row, add a string to the second list that starts with `row N:` where **N is the 1-based row number**, followed by anything helpful (for example the field name and Pydantic's message).
- Never let a `ValidationError` escape.

Example:

```python
users, errors = parse_users([
    {"name": "Ada", "age": 36, "email": "ada@example.com"},
    {"name": "", "age": 200, "email": "nope"},
])
users   # [User(name='Ada', age=36, email='ada@example.com', tags=[])]
errors  # ['row 2: name: String should have at least 1 character; age: ...; email: ...']
```

Note that Pydantic converts compatible types for you: `"36"` becomes `36` for an `int` field.
