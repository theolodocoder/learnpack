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
    # TODO: with conn:
    # TODO:     insert the document (body = "\n\n".join(chunks)), get lastrowid
    # TODO:     executemany the chunk rows (document_id, position, text)
    raise NotImplementedError


def chunks_for(conn: sqlite3.Connection, title: str) -> list[str]:
    """Chunk texts for the document with this title, in position order."""
    # TODO: SELECT c.text FROM chunks c JOIN documents d ON ... WHERE d.title = ? ORDER BY c.position
    raise NotImplementedError


def chunk_counts(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """(title, number of chunks) for every document, ordered by title."""
    # TODO: LEFT JOIN + GROUP BY + COUNT(c.id)
    raise NotImplementedError


if __name__ == "__main__":
    conn = connect()
    try:
        save_document(conn, "Refunds", ["Refunds within 30 days.", "Gifts get store credit."])
        save_document(conn, "Empty", [])
        print(chunks_for(conn, "Refunds"))
        print(chunk_counts(conn))
    except NotImplementedError:
        print("Write the three functions, then Run again.")
