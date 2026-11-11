from fastapi.testclient import TestClient

import solution
from solution import app

client = TestClient(app)


def fresh():
    solution.notes.clear()


def test_create_returns_201_with_id():
    fresh()
    r = client.post("/notes", json={"title": "Groceries", "body": "rice, beans"})
    assert r.status_code == 201, f"POST /notes should return 201, got {r.status_code}: {r.text}"
    want = {"title": "Groceries", "body": "rice, beans", "id": 1}
    assert r.json() == want, f"expected {want!r}, got {r.json()!r}"
    r2 = client.post("/notes", json={"title": "Second"})
    assert r2.json() == {"title": "Second", "body": "", "id": 2}, f"body defaults to '' and ids go up by one, got {r2.json()!r}"


def test_read_note_and_404():
    fresh()
    client.post("/notes", json={"title": "Groceries"})
    r = client.get("/notes/1")
    assert r.status_code == 200 and r.json()["title"] == "Groceries", f"GET /notes/1 failed: {r.status_code} {r.text}"
    r = client.get("/notes/99")
    assert r.status_code == 404, f"a missing note should be 404, got {r.status_code}"
    assert r.json() == {"detail": "Note not found"}, f"expected detail 'Note not found', got {r.json()!r}"


def test_invalid_title_is_422():
    fresh()
    for body in ({"title": ""}, {"body": "no title"}, {"title": "x" * 101}):
        r = client.post("/notes", json=body)
        assert r.status_code == 422, f"{body!r} should be rejected with 422, got {r.status_code}"
    assert solution.notes == {}, "invalid notes must not be stored"


def test_list_filters_by_title_ignoring_case():
    fresh()
    for t in ["Groceries", "Gym plan", "grocery budget"]:
        client.post("/notes", json={"title": t})
    r = client.get("/notes", params={"q": "GROC"})
    titles = [n["title"] for n in r.json()]
    assert titles == ["Groceries", "grocery budget"], f"expected the two grocery notes in id order, got {titles!r}"


def test_list_limit_and_bounds():
    fresh()
    for i in range(15):
        client.post("/notes", json={"title": f"note {i}"})
    r = client.get("/notes")
    assert len(r.json()) == 10, f"default limit is 10, got {len(r.json())}"
    assert [n["id"] for n in client.get("/notes", params={"limit": 3}).json()] == [1, 2, 3], "limit=3 should give ids 1, 2, 3"
    for bad in (0, 51):
        code = client.get("/notes", params={"limit": bad}).status_code
        assert code == 422, f"limit={bad} should be rejected with 422, got {code}"
