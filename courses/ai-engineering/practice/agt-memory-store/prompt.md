# Long-term memory: save facts, recall them by meaning

Conversation history is short-term memory: it disappears when the session ends. Long-term memory is a **store of facts** the agent saves on purpose ("Ada prefers Postgres", "invoice #88 was refunded") and recalls later with the retrieval you built for RAG.

Build a small SQLite-backed memory:

```python
class MemoryStore:
    def __init__(self, embed, path: str = ":memory:"): ...
    def remember(self, user_id: str, fact: str) -> int: ...
    def recall(self, user_id: str, query: str, k: int = 3, min_score: float = 0.2) -> list[str]: ...
    def forget(self, user_id: str, fact_id: int) -> bool: ...
```

- `embed` is a function that takes a list of strings and returns a NumPy array of L2-normalised rows (like `fake_embed.embed`, or a real embedding model). Inject it; don't import one.
- Use `sqlite3` with a table `memories(id INTEGER PRIMARY KEY, user_id TEXT, fact TEXT, vector BLOB)`. Store the vector as `vec.astype(np.float32).tobytes()` and read it back with `np.frombuffer(blob, dtype=np.float32)`. Commit after writes so another `MemoryStore` on the same file sees them.
- `remember` stores the fact and its embedding, and returns the new row id.
- `recall` embeds the query, scores **only that user's** facts by dot product (cosine, since rows are normalised), drops those below `min_score`, and returns the top `k` fact strings, best first.
- `forget` deletes a fact if it belongs to that user, and returns whether a row was deleted.
- Always use `?` placeholders in SQL.

## Example

```python
from fake_embed import embed
mem = MemoryStore(embed)
mem.remember("ada", "Ada's database is Postgres 16")
mem.remember("ada", "Ada prefers short answers")
mem.remember("bo", "Bo's database is MySQL")
mem.recall("ada", "which database does she use?")
# ["Ada's database is Postgres 16"]
```
