# SQL and Postgres

## Why this matters

Every real AI product stores things: users, uploaded documents, chunks of those documents, conversation history, usage and cost per customer. That data lives in a relational database, and the default choice for new projects is PostgreSQL. With the `pgvector` extension, Postgres also stores embeddings and does similarity search, so one database holds both your normal data and your RAG index. You need enough SQL to design a few tables, query them safely from Python, and not get hacked by the first user who types an apostrophe.

## 1. Tables, rows and types

A relational database holds **tables**. A table has named, typed **columns**, and each **row** is one record. You define a table with `CREATE TABLE`:

```sql
CREATE TABLE documents (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL UNIQUE,
    body        TEXT NOT NULL,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
```

- `PRIMARY KEY` uniquely identifies each row. Let the database assign it.
- `NOT NULL` forbids missing values; `UNIQUE` forbids duplicates. These are **constraints**: rules the database enforces no matter which program writes to it. That's stronger than checking in Python, because every code path is covered.
- `DEFAULT` fills a value when you don't supply one.

To practise without installing anything, Python ships with **SQLite**, a complete SQL database in a single file (or in memory). The SQL you write is almost identical to Postgres; section 7 covers the differences.

```python
import sqlite3

conn = sqlite3.connect(":memory:")  # or "app.db" for a file on disk
conn.execute("""
    CREATE TABLE documents (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL UNIQUE,
        body TEXT NOT NULL
    )
""")
```

## 2. INSERT and SELECT, with parameters

Add rows with `INSERT` and read them with `SELECT`:

```python
cur = conn.execute("INSERT INTO documents (title, body) VALUES (?, ?)",
                   ("Refund policy", "Refunds are accepted within 30 days."))
print(cur.lastrowid)  # 1: the id the database assigned
conn.execute("INSERT INTO documents (title, body) VALUES (?, ?)",
             ("Shipping", "We ship to Lagos, Abuja and Accra."))
conn.commit()

rows = conn.execute("SELECT id, title FROM documents").fetchall()
print(rows)  # [(1, 'Refund policy'), (2, 'Shipping')]
```

The `?` marks are **placeholders**. You pass the values separately as a tuple, and the database driver sends them to the database *as data*, never as part of the SQL text. This is the single most important habit in this lesson (section 4 explains why).

`conn.execute` returns a **cursor**: `.fetchall()` gives a list of tuples, `.fetchone()` gives one tuple or `None`. `conn.commit()` makes your changes permanent.

## 3. Filtering, sorting, limiting

```sql
SELECT id, title FROM documents
WHERE body LIKE '%refund%'      -- filter rows
ORDER BY title                  -- sort (add DESC for descending)
LIMIT 10;                       -- at most 10 rows
```

- `WHERE` accepts comparisons (`=`, `<>`, `<`, `>=`), `AND`, `OR`, `IN (...)`, `IS NULL`, and `LIKE` with `%` meaning "any characters".
- `ORDER BY` is the only way to get a guaranteed order. Without it the database returns rows in whatever order is convenient, which can change.
- `LIMIT` caps the result size. Always limit queries that feed an API.

From Python, every value that comes from outside (user input, a file, an API) goes through a placeholder, including the `%` wildcards:

```python
term = "refund"
rows = conn.execute(
    "SELECT id, title FROM documents WHERE title LIKE ? ORDER BY title LIMIT ?",
    (f"%{term}%", 10),
).fetchall()
```

Update and delete use the same `WHERE` syntax. Forget the `WHERE` and you change *every* row:

```sql
UPDATE documents SET body = 'New text' WHERE id = 1;
DELETE FROM documents WHERE id = 2;
```

## 4. SQL injection: why placeholders are not optional

Suppose you build the query with an f-string:

```python
title = input("Title to search: ")
conn.execute(f"SELECT * FROM documents WHERE title = '{title}'")   # NEVER do this
```

A user types `x' OR '1'='1`. Your SQL becomes:

```sql
SELECT * FROM documents WHERE title = 'x' OR '1'='1'
```

and returns every document, including other customers' private ones. With a little more effort an attacker can read other tables or delete data. This is **SQL injection**, and it has been one of the most common security holes on the web for twenty-five years.

With a placeholder the same input is harmless: the database looks for a document whose title is literally the string `x' OR '1'='1` and finds none. It also fixes the honest case: a title like `O'Reilly notes` breaks the f-string version with a syntax error and works fine with `?`.

The rule: **SQL text is written by you; values always go through placeholders.** Placeholders work for values only, not for table or column names. If you must choose a column dynamically (say, a sort field), check it against a fixed allow-list in Python first.

> **Note:** LLM apps add a twist. If a model generates SQL from a user's question ("text-to-SQL"), treat the generated SQL as untrusted: run it with a read-only database user, on an allow-listed set of tables, with a row limit.

## 5. Relationships and JOIN

In RAG, one document is split into many **chunks**. That's a one-to-many relationship, modelled with a **foreign key**:

```sql
CREATE TABLE chunks (
    id          INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    text        TEXT NOT NULL
);
```

`REFERENCES documents(id)` says each chunk belongs to a document. `ON DELETE CASCADE` deletes a document's chunks when the document is deleted. (SQLite only enforces foreign keys after `PRAGMA foreign_keys = ON`; Postgres always does.)

A **JOIN** combines rows from two tables where a condition matches:

```sql
SELECT d.title, c.position, c.text
FROM chunks AS c
JOIN documents AS d ON d.id = c.document_id
WHERE d.title = 'Refund policy'
ORDER BY c.position;
```

`JOIN` (an inner join) keeps only rows that match on both sides. A **LEFT JOIN** keeps every row from the left table, with `NULL`s where nothing matches. Combine it with `GROUP BY` and `COUNT` to summarise:

```sql
SELECT d.title, COUNT(c.id) AS n_chunks
FROM documents AS d
LEFT JOIN chunks AS c ON c.document_id = d.id
GROUP BY d.id
ORDER BY d.title;
-- Refund policy | 3
-- Shipping      | 0     <- kept thanks to LEFT JOIN; COUNT(c.id) ignores NULLs
```

## 6. Indexes and transactions

### Indexes

Without an index, `WHERE document_id = 5` reads every row in `chunks`. An **index** is a sorted lookup structure (usually a B-tree) that finds matching rows quickly, like the index at the back of a book:

```sql
CREATE INDEX idx_chunks_document ON chunks (document_id);
```

Index the columns you filter or join on often. Primary keys and `UNIQUE` columns are indexed automatically. Indexes aren't free: they use disk and slow down writes slightly, so don't index everything. You'll meet a very different kind of index, for vectors, at the end of this lesson.

### Transactions

Saving a document means one `INSERT` into `documents` and many into `chunks`. If the program crashes after half the chunks, you have a broken document. A **transaction** groups statements so they all succeed or none do:

```python
def save_document(conn, title: str, chunks: list[str]) -> int:
    with conn:  # commits if the block succeeds, rolls back if it raises
        doc_id = conn.execute("INSERT INTO documents (title, body) VALUES (?, ?)",
                              (title, "\n\n".join(chunks))).lastrowid
        conn.executemany(
            "INSERT INTO chunks (document_id, position, text) VALUES (?, ?, ?)",
            [(doc_id, i, text) for i, text in enumerate(chunks)],
        )
    return doc_id
```

`with conn:` is sqlite3's transaction context manager: on success it commits; on an exception it **rolls back** every change made in the block and re-raises. `executemany` runs one statement for many parameter tuples, which is faster than a loop of `execute` calls.

> **Try it:** In the second exercise, make one chunk an empty string and check that no document was saved. That's the rollback working: the `CHECK` constraint on the chunk text failed on a later insert and undid the earlier ones.

## 7. Postgres for real (via Docker)

SQLite is perfect for learning, tests and small tools. For a web backend with many users writing at once, use **PostgreSQL**: it handles concurrent writers, has richer types (JSON, arrays, timestamps with time zones), full-text search, and extensions like **pgvector**.

You don't need to install Postgres. Run it in Docker with pgvector already included:

```bash
docker run --name pg -e POSTGRES_PASSWORD=devpassword -p 5432:5432 -d pgvector/pgvector:pg17
docker exec -it pg psql -U postgres     # an interactive SQL prompt inside the container
```

`-p 5432:5432` exposes Postgres on `localhost:5432`; `-d` runs it in the background. `docker stop pg` / `docker start pg` stop and restart it, keeping data until you `docker rm pg`. (In the project you'll use a `docker-compose.yml` with a volume so data survives.)

From Python, the standard driver is **psycopg** (version 3): `pip install "psycopg[binary]"`. The code looks almost the same as sqlite3:

```python
import psycopg

with psycopg.connect("postgresql://postgres:devpassword@localhost:5432/postgres") as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          BIGSERIAL PRIMARY KEY,
            title       TEXT NOT NULL UNIQUE,
            body        TEXT NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    doc_id = conn.execute(
        "INSERT INTO documents (title, body) VALUES (%s, %s) RETURNING id",
        ("Refund policy", "Refunds are accepted within 30 days."),
    ).fetchone()[0]
    rows = conn.execute("SELECT id, title FROM documents WHERE title ILIKE %s", ("%refund%",)).fetchall()
# leaving the `with` block commits (or rolls back on an exception) and closes the connection
```

The differences that matter day to day:

| | SQLite (`sqlite3`) | Postgres (`psycopg`) |
|---|---|---|
| Placeholder | `?` | `%s` (still a placeholder: never use Python `%` formatting) |
| Auto-increment id | `INTEGER PRIMARY KEY` | `BIGSERIAL` or `GENERATED ALWAYS AS IDENTITY` |
| New id after insert | `cursor.lastrowid` | `INSERT ... RETURNING id` |
| Timestamps | text | `TIMESTAMPTZ`, `now()` |
| Case-insensitive LIKE | `LIKE` (ASCII) | `ILIKE` |
| Types enforced | loosely | strictly |
| Concurrency | one writer at a time | many |
| Runs as | a library in your process | a server you connect to |

For async FastAPI handlers, psycopg also has `await psycopg.AsyncConnection.connect(...)` and a connection pool (`psycopg_pool`). Open the pool once at startup and hand out connections through a dependency, just like the LLM client in the previous lesson.

### A first look at pgvector

pgvector adds a `vector` column type and distance operators. Enable it once per database, then store embeddings next to your chunks:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id          BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position    INT NOT NULL,
    text        TEXT NOT NULL,
    embedding   vector(1024) NOT NULL
);

CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
```

`vector(1024)` matches a 1024-dimensional embedding model. The HNSW index makes nearest-neighbour search fast on millions of rows. The *Embeddings and semantic search* and *RAG from scratch* lessons cover what goes in that column and how to query it.

## Common mistakes

- **Building SQL with f-strings or `+`.** SQL injection, and broken queries on apostrophes. Always use placeholders.
- **Using `%` string formatting with psycopg.** `%s` in psycopg is a placeholder; pass values as the second argument, never `query % values`.
- **Forgetting to commit** in sqlite3: your inserts vanish when the connection closes. Use `with conn:`.
- **No `ORDER BY`** and then relying on row order.
- **`UPDATE` or `DELETE` without `WHERE`.** Test the `WHERE` with a `SELECT` first.
- **Inserting related rows without a transaction**, leaving half-saved documents after a crash.
- **Indexing nothing** (slow queries) or **everything** (slow writes).

## Recap

- Tables have typed columns and constraints (`PRIMARY KEY`, `NOT NULL`, `UNIQUE`, `REFERENCES`) that the database enforces.
- `INSERT`, `SELECT ... WHERE ... ORDER BY ... LIMIT`, `UPDATE`, `DELETE` cover most work; `JOIN` combines related tables, `LEFT JOIN` keeps unmatched rows.
- Values always go through placeholders (`?` in sqlite3, `%s` in psycopg). That's what prevents SQL injection.
- Indexes speed up lookups on the columns you filter and join on; transactions (`with conn:`) make multi-step writes all-or-nothing.
- Practise with in-memory `sqlite3`; run Postgres with pgvector in Docker (`pgvector/pgvector:pg17`) for real apps, and connect with psycopg.
