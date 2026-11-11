from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=0, le=150)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    tags: list[str] = Field(default_factory=list)


def parse_users(rows: list[dict]) -> tuple[list[User], list[str]]:
    """Validate every row. Return (valid users, error strings starting 'row N:')."""
    users: list[User] = []
    errors: list[str] = []
    for n, row in enumerate(rows, start=1):
        try:
            users.append(User.model_validate(row))
        except ValidationError as err:
            details = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in err.errors())
            errors.append(f"row {n}: {details}")
    return users, errors


if __name__ == "__main__":
    users, errors = parse_users([
        {"name": "Ada", "age": 36, "email": "ada@example.com"},
        {"name": "", "age": 200, "email": "nope"},
    ])
    print(users)
    print(errors)
