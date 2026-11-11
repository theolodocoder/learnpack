import sqlite3

import numpy as np


class MemoryStore:
    def __init__(self, embed, path: str = ":memory:"):
        self.embed = embed
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS memories("
            "id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, fact TEXT NOT NULL, vector BLOB NOT NULL)"
        )
        self.db.commit()

    def remember(self, user_id: str, fact: str) -> int:
        vec = np.asarray(self.embed([fact])[0], dtype=np.float32)
        cur = self.db.execute("INSERT INTO memories(user_id, fact, vector) VALUES (?, ?, ?)",
                              (user_id, fact, vec.tobytes()))
        self.db.commit()
        return cur.lastrowid

    def recall(self, user_id: str, query: str, k: int = 3, min_score: float = 0.2) -> list[str]:
        q = np.asarray(self.embed([query])[0], dtype=np.float32)
        rows = self.db.execute("SELECT fact, vector FROM memories WHERE user_id = ?", (user_id,)).fetchall()
        # ponytail: scores every fact for this user in Python; use a vector index (pgvector) past ~100k facts
        scored = [(float(np.frombuffer(blob, dtype=np.float32) @ q), fact) for fact, blob in rows]
        scored = [s for s in scored if s[0] >= min_score]
        scored.sort(key=lambda s: s[0], reverse=True)
        return [fact for _, fact in scored[:k]]

    def forget(self, user_id: str, fact_id: int) -> bool:
        cur = self.db.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (fact_id, user_id))
        self.db.commit()
        return cur.rowcount > 0
