import sqlite3


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the documents table (id, title UNIQUE NOT NULL, body NOT NULL)."""
    # TODO: conn.execute("CREATE TABLE ...")
    pass


def add_document(conn: sqlite3.Connection, title: str, body: str) -> int:
    """Insert a document, commit, return its new id."""
    # TODO: use ? placeholders, then conn.commit()
    raise NotImplementedError


def find_documents(conn: sqlite3.Connection, term: str, limit: int = 10) -> list[tuple[int, str]]:
    """(id, title) of documents whose title contains term, ordered by title, at most limit."""
    # TODO: WHERE title LIKE ? ... ORDER BY title LIMIT ?  with (f"%{term}%", limit)
    raise NotImplementedError


if __name__ == "__main__":
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    try:
        add_document(conn, "Refund policy", "Refunds within 30 days.")
        add_document(conn, "O'Reilly notes", "Quotes must not break anything.")
        print(find_documents(conn, "refund"))
        print(find_documents(conn, "x' OR '1'='1"))
    except NotImplementedError:
        print("Write add_document and find_documents, then Run again.")
