# Documents, chunks, JOINs and a transaction

A RAG app stores each document plus the chunks it was split into. The schema is given in the starter (`documents` and `chunks`, where `chunks.document_id` references `documents.id`). Write:

```python
def save_document(conn, title: str, chunks: list[str]) -> int: ...
def chunks_for(conn, title: str) -> list[str]: ...
def chunk_counts(conn) -> list[tuple[str, int]]: ...
```

1. **`save_document`** inserts the document (its `body` is the chunks joined with `"\n\n"`) and one `chunks` row per chunk with `position` 0, 1, 2, ... **in a single transaction** (`with conn:`). If any insert fails (the schema has a `CHECK` that rejects empty chunk text), nothing is saved and the exception propagates. Returns the document id.
2. **`chunks_for`** returns the chunk texts of the document with that title, in `position` order, using a **JOIN** between `chunks` and `documents`. An unknown title gives `[]`.
3. **`chunk_counts`** returns `(title, number_of_chunks)` for **every** document, including ones with zero chunks, ordered by title. Use `LEFT JOIN` and `GROUP BY`.

## Example

```python
save_document(conn, "Refunds", ["Refunds within 30 days.", "Gifts get store credit."])   # 1
save_document(conn, "Empty", [])                                                         # 2
chunks_for(conn, "Refunds")      # ['Refunds within 30 days.', 'Gifts get store credit.']
chunk_counts(conn)               # [('Empty', 0), ('Refunds', 2)]
save_document(conn, "Broken", ["ok", ""])     # raises sqlite3.IntegrityError (CHECK: text not empty)
chunk_counts(conn)               # unchanged: "Broken" was rolled back
```
