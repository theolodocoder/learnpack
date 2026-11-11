import os
import tempfile

from fake_embed import embed
from solution import MemoryStore


def filled():
    mem = MemoryStore(embed)
    ids = [mem.remember("ada", "Ada's database is Postgres 16"),
           mem.remember("ada", "Ada prefers short answers"),
           mem.remember("ada", "Ada's bakery sells sourdough bread"),
           mem.remember("bo", "Bo's database is MySQL")]
    return mem, ids


def test_remember_returns_distinct_ids():
    _, ids = filled()
    assert all(isinstance(i, int) for i in ids) and len(set(ids)) == 4, f"expected 4 distinct int ids, got {ids!r}"


def test_recall_finds_the_relevant_fact_first():
    mem, _ = filled()
    got = mem.recall("ada", "what database does Ada use?")
    assert got and got[0] == "Ada's database is Postgres 16", f"expected the Postgres fact first, got {got!r}"


def test_recall_is_scoped_to_the_user():
    mem, _ = filled()
    got = mem.recall("ada", "database", k=5)
    assert "Bo's database is MySQL" not in got, f"never return another user's memories, got {got!r}"
    assert mem.recall("carol", "database") == [], "a user with no memories gets []"


def test_min_score_and_k_limit_results():
    mem, _ = filled()
    assert mem.recall("ada", "quantum chromodynamics") == [], "unrelated queries should return nothing"
    got = mem.recall("ada", "Ada database bakery answers", k=2, min_score=0.0)
    assert len(got) == 2, f"return at most k facts, got {got!r}"


def test_forget_only_deletes_own_fact():
    mem, ids = filled()
    assert mem.forget("bo", ids[0]) is False, "bo must not be able to delete ada's fact"
    assert mem.forget("ada", ids[0]) is True, "forget should return True when it deletes"
    got = mem.recall("ada", "what database does Ada use?")
    assert "Ada's database is Postgres 16" not in got, f"forgotten facts must not be recalled, got {got!r}"


def test_memories_persist_in_a_file():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "memory.db")
        MemoryStore(embed, path).remember("ada", "Ada's database is Postgres 16")
        got = MemoryStore(embed, path).recall("ada", "database")
        assert got == ["Ada's database is Postgres 16"], f"a new store on the same file should see saved facts, got {got!r}"
