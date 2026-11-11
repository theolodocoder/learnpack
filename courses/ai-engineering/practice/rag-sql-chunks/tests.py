import sqlite3

from solution import chunk_counts, chunks_for, connect, save_document


def test_save_and_read_chunks_in_order():
    conn = connect()
    doc_id = save_document(conn, "Refunds", ["first", "second", "third"])
    assert doc_id == 1, f"expected document id 1, got {doc_id!r}"
    got = chunks_for(conn, "Refunds")
    assert got == ["first", "second", "third"], f"expected chunks in position order, got {got!r}"
    body = conn.execute("SELECT body FROM documents WHERE id = 1").fetchone()[0]
    assert body == "first\n\nsecond\n\nthird", f"body should be the chunks joined by blank lines, got {body!r}"


def test_chunks_for_only_returns_that_document():
    conn = connect()
    save_document(conn, "Refunds", ["r1", "r2"])
    save_document(conn, "Shipping", ["s1"])
    assert chunks_for(conn, "Shipping") == ["s1"], f"got {chunks_for(conn, 'Shipping')!r}"
    assert chunks_for(conn, "Nope") == [], "an unknown title should give []"


def test_counts_include_documents_without_chunks():
    conn = connect()
    save_document(conn, "Refunds", ["a", "b"])
    save_document(conn, "Empty", [])
    save_document(conn, "About", ["x"])
    got = chunk_counts(conn)
    want = [("About", 1), ("Empty", 0), ("Refunds", 2)]
    assert got == want, f"expected {want!r} (LEFT JOIN keeps 'Empty'), got {got!r}"


def test_failed_save_is_rolled_back():
    conn = connect()
    save_document(conn, "Good", ["ok"])
    try:
        save_document(conn, "Broken", ["fine", ""])
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("an empty chunk should raise sqlite3.IntegrityError (the CHECK on chunks.text)")
    titles = [t for (t,) in conn.execute("SELECT title FROM documents ORDER BY title")]
    assert titles == ["Good"], f"'Broken' must be rolled back completely, but documents has {titles!r}"
    n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    assert n == 1, f"no chunks of 'Broken' should remain, but chunks has {n} rows"


def test_quotes_are_safe():
    conn = connect()
    save_document(conn, "Ade's notes", ["it's fine"])
    assert chunks_for(conn, "Ade's notes") == ["it's fine"], "use ? placeholders so quotes work"
    assert chunks_for(conn, "x' OR '1'='1") == [], "the title must be treated as data, not SQL"
