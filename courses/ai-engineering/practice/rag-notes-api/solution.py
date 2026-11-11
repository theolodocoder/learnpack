from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str = ""


class Note(NoteIn):
    id: int


notes: dict[int, Note] = {}
app = FastAPI(title="Notes API")


@app.post("/notes", status_code=201)
def create_note(note: NoteIn) -> Note:
    new = Note(id=max(notes, default=0) + 1, **note.model_dump())
    notes[new.id] = new
    return new


@app.get("/notes/{note_id}")
def read_note(note_id: int) -> Note:
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="Note not found")
    return notes[note_id]


@app.get("/notes")
def list_notes(q: str | None = None, limit: Annotated[int, Query(ge=1, le=50)] = 10) -> list[Note]:
    found = [n for _, n in sorted(notes.items())]
    if q:
        found = [n for n in found if q.lower() in n.title.lower()]
    return found[:limit]


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.post("/notes", json={"title": "Groceries", "body": "rice, beans"})
    print(r.status_code, r.json())
    print(client.get("/notes/1").status_code, client.get("/notes/1").json())
    print(client.get("/notes", params={"limit": 0}).json())
