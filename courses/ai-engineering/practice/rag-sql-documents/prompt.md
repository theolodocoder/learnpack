# Store and search documents safely with sqlite3

Write three functions that work on a `sqlite3` connection. Every value from outside must go through `?` placeholders.

```python
def create_schema(conn: sqlite3.Connection) -> None: ...
def add_document(conn: sqlite3.Connection, title: str, body: str) -> int: ...
def find_documents(conn: sqlite3.Connection, term: str, limit: int = 10) -> list[tuple[int, str]]: ...
```

1. **`create_schema`** creates a `documents` table with `id INTEGER PRIMARY KEY`, `title TEXT NOT NULL UNIQUE` and `body TEXT NOT NULL`.
2. **`add_document`** inserts a row, commits, and returns the new id (`cursor.lastrowid`). A duplicate title should raise `sqlite3.IntegrityError` (the `UNIQUE` constraint does this for you; don't catch it).
3. **`find_documents`** returns `(id, title)` tuples for documents whose **title** contains `term` (`LIKE` with `%` on both sides, which is case-insensitive for ASCII in SQLite), ordered by title, at most `limit` rows.

Titles with quotes, like `O'Reilly notes`, must work, and a search for `x' OR '1'='1` must return `[]`, not every row.

## Example

```python
conn = sqlite3.connect(":memory:")
create_schema(conn)
add_document(conn, "Refund policy", "30 days.")      # 1
add_document(conn, "Shipping rates", "Flat fee.")    # 2
find_documents(conn, "refund")                       # [(1, 'Refund policy')]
find_documents(conn, "x' OR '1'='1")                 # []
```
