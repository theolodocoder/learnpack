# A small notes API

Build a FastAPI app that stores notes in memory. Everything lives in one module:

```python
class NoteIn(BaseModel): ...      # what the client sends
class Note(NoteIn): ...           # what the API returns: NoteIn plus an id
notes: dict[int, Note] = {}       # the "database"
app = FastAPI()
```

1. **`NoteIn`** has `title: str` (1 to 100 characters) and `body: str` (optional, default `""`). **`Note`** adds `id: int`.
2. **`POST /notes`** takes a `NoteIn` body, stores a new `Note` and returns it with status **201**. Ids start at 1 and go up by one: use `max(notes, default=0) + 1`.
3. **`GET /notes/{note_id}`** returns that note, or **404** with `{"detail": "Note not found"}`.
4. **`GET /notes`** returns a list of notes ordered by id, with two optional query parameters:
   - `q`: keep only notes whose title contains `q`, ignoring case;
   - `limit`: an `int` from 1 to 50 (default 10), the maximum number of notes to return. Out of range gives FastAPI's automatic **422**.

Invalid bodies (like an empty title) must get a 422 automatically: you don't need any code for that beyond the model.

## Example

```python
client = TestClient(app)
client.post("/notes", json={"title": "Groceries"})       # 201 {"title": "Groceries", "body": "", "id": 1}
client.get("/notes/1").json()["title"]                  # "Groceries"
client.get("/notes/99").status_code                     # 404
client.get("/notes", params={"q": "GROC"}).json()       # [{"title": "Groceries", "body": "", "id": 1}]
client.get("/notes", params={"limit": 0}).status_code   # 422
```

The tests clear `notes` before each test, so keep the store in that module-level dict.
