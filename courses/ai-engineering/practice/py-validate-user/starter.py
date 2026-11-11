from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    # TODO: add constraints with Field(...)
    name: str
    age: int
    email: str
    tags: list[str] = []


def parse_users(rows: list[dict]) -> tuple[list[User], list[str]]:
    """Validate every row. Return (valid users, error strings starting 'row N:')."""
    users: list[User] = []
    errors: list[str] = []
    # TODO: enumerate(rows, start=1); try User.model_validate(row);
    #       on ValidationError, build a message from err.errors() (each has "loc" and "msg")
    return users, errors


if __name__ == "__main__":
    users, errors = parse_users([
        {"name": "Ada", "age": 36, "email": "ada@example.com"},
        {"name": "", "age": 200, "email": "nope"},
    ])
    print(users)
    print(errors)
