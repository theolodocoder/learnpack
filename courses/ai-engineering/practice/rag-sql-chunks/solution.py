import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id    INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    body  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    text        TEXT NOT NULL CHECK (length(text) > 0)
);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks (document_id);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def save_document(conn: sqlite3.Connection, title: str, chunks: list[str]) -> int:
    """Insert a document and its chunks atomically. Returns the document id."""
    with conn:
        doc_id = conn.execute(
            "INSERT INTO documents (title, body) VALUES (?, ?)", (title, "\n\n".join(chunks))
        ).lastrowid
        conn.executemany(
            "INSERT INTO chunks (document_id, position, text) VALUES (?, ?, ?)",
            [(doc_id, i, text) for i, text in enumerate(chunks)],
        )
    return doc_id


def chunks_for(conn: sqlite3.Connection, title: str) -> list[str]:
    """Chunk texts for the document with this title, in position order."""
    rows = conn.execute(
        """SELECT c.text FROM chunks AS c
           JOIN documents AS d ON d.id = c.document_id
           WHERE d.title = ?
           ORDER BY c.position""",
        (title,),
    ).fetchall()
    return [text for (text,) in rows]


def chunk_counts(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """(title, number of chunks) for every document, ordered by title."""
    return conn.execute(
        """SELECT d.title, COUNT(c.id) FROM documents AS d
           LEFT JOIN chunks AS c ON c.document_id = d.id
           GROUP BY d.id
           ORDER BY d.title"""
    ).fetchall()


if __name__ == "__main__":
    conn = connect()
    save_document(conn, "Refunds", ["Refunds within 30 days.", "Gifts get store credit."])
    save_document(conn, "Empty", [])
    print(chunks_for(conn, "Refunds"))
    print(chunk_counts(conn))
