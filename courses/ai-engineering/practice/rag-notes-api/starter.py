from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


class NoteIn(BaseModel):
    # TODO: title (1-100 chars) and body (default "")
    pass


class Note(NoteIn):
    # TODO: add id
    pass


notes: dict[int, Note] = {}
app = FastAPI(title="Notes API")


@app.post("/notes", status_code=201)
def create_note(note: NoteIn) -> Note:
    # TODO: pick the next id, build a Note, store it, return it
    raise HTTPException(status_code=501, detail="Not implemented yet")


# TODO: GET /notes/{note_id}  -> the note, or 404 "Note not found"


# TODO: GET /notes?q=...&limit=...  -> list[Note] ordered by id


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r = client.post("/notes", json={"title": "Groceries", "body": "rice, beans"})
    print(r.status_code, r.json())
    print(client.get("/notes/1").status_code, client.get("/notes/1").json())
    print(client.get("/notes", params={"limit": 0}).json())
