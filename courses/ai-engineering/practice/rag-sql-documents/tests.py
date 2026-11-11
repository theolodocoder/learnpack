import sqlite3

from solution import add_document, create_schema, find_documents


def fresh():
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    return conn


def test_add_returns_increasing_ids():
    conn = fresh()
    ids = [add_document(conn, t, "body") for t in ("Refund policy", "Shipping rates", "Opening hours")]
    assert ids == [1, 2, 3], f"expected ids [1, 2, 3], got {ids!r}"
    n = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    assert n == 3, f"expected 3 rows in documents, got {n}"


def test_find_matches_title_ordered():
    conn = fresh()
    for t in ("Shipping rates", "Refund policy", "Refunds for gifts", "Opening hours"):
        add_document(conn, t, "body")
    got = find_documents(conn, "REFUND")
    want = [(2, "Refund policy"), (3, "Refunds for gifts")]
    assert got == want, f"expected {want!r} (case-insensitive, ordered by title), got {got!r}"


def test_limit_is_respected():
    conn = fresh()
    for i in range(5):
        add_document(conn, f"Note {i}", "body")
    got = find_documents(conn, "Note", limit=2)
    assert got == [(1, "Note 0"), (2, "Note 1")], f"limit=2 should give the first two by title, got {got!r}"


def test_quotes_in_titles_work():
    conn = fresh()
    doc_id = add_document(conn, "O'Reilly notes", "It's fine.")
    got = find_documents(conn, "O'Reilly")
    assert got == [(doc_id, "O'Reilly notes")], f"titles with apostrophes must work, got {got!r}"


def test_injection_attempt_returns_nothing():
    conn = fresh()
    add_document(conn, "Private: salaries", "secret")
    add_document(conn, "Public FAQ", "hello")
    got = find_documents(conn, "x' OR '1'='1")
    assert got == [], f"the search term must be treated as data, not SQL; got {got!r}"


def test_duplicate_title_raises_integrity_error():
    conn = fresh()
    add_document(conn, "Refund policy", "v1")
    try:
        add_document(conn, "Refund policy", "v2")
    except sqlite3.IntegrityError:
        return
    raise AssertionError("a duplicate title should raise sqlite3.IntegrityError (title is UNIQUE)")
