import sqlite3

import numpy as np


class MemoryStore:
    def __init__(self, embed, path: str = ":memory:"):
        self.embed = embed
        self.db = sqlite3.connect(path)
        # TODO: CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY, user_id TEXT, fact TEXT, vector BLOB)

    def remember(self, user_id: str, fact: str) -> int:
        # TODO: vec = self.embed([fact])[0]; INSERT with ? placeholders; commit; return cursor.lastrowid
        raise NotImplementedError

    def recall(self, user_id: str, query: str, k: int = 3, min_score: float = 0.2) -> list[str]:
        # TODO: embed the query; SELECT this user's facts and vectors
        # TODO: score = vector @ query_vector; keep score >= min_score; best first; top k fact strings
        raise NotImplementedError

    def forget(self, user_id: str, fact_id: int) -> bool:
        # TODO: DELETE ... WHERE id = ? AND user_id = ?; commit; return cursor.rowcount > 0
        raise NotImplementedError


if __name__ == "__main__":
    from fake_embed import embed

    mem = MemoryStore(embed)
    try:
        mem.remember("ada", "Ada's database is Postgres 16")
        mem.remember("ada", "Ada prefers short answers")
        mem.remember("bo", "Bo's database is MySQL")
        print(mem.recall("ada", "which database does she use?"))
    except NotImplementedError:
        print("Write the MemoryStore methods first, then Run again.")
