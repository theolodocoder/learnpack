# Chat with your docs API

Build a backend that lets someone upload documents and then ask questions about them, getting answers grounded in those documents with citations to the exact passages used. It's FastAPI in front, Postgres with pgvector for storage and search, an embedding model for retrieval, and Claude for the answers, all tested offline with fakes and deployed to a public URL.

This is probably the single most common paid AI gig right now: "an AI chatbot for our docs", "a support assistant trained on our help centre", "ask questions about our policies / contracts / product manuals". Businesses of every size ask for it, on freelance platforms and in internship interviews alike. A clean, tested, deployed version with real citations and an honest "I don't know" is exactly the portfolio piece that wins that work.

Build it in **its own GitHub repository**, then paste the repo URL and your live URL into the fields below.

## Requirements

1. **Upload:** `POST /documents` accepts a document (a `.md` or `.txt` file upload, or JSON `{"title": ..., "text": ...}`; PDF is a stretch goal). It cleans, chunks, embeds and stores it, and returns the document id and number of chunks. Re-uploading a document with the same title replaces its chunks instead of duplicating them.
2. **List and delete:** `GET /documents` lists documents with their chunk counts; `DELETE /documents/{id}` removes a document and its chunks (`ON DELETE CASCADE`).
3. **Ask:** `POST /ask` takes `{"question": ..., "k": 5}` and returns `{"answer": ..., "sources": [{"id", "document", "heading", "text", "score"}]}`. Sources are only chunks that were retrieved *and* cited.
4. **"I don't know":** if no chunk passes a similarity threshold, return a clear "I don't know" answer with no sources, **without calling Claude**. Calibrate the threshold on your own questions and note the value and how you chose it in the README.
5. **Storage:** Postgres with pgvector, running in Docker through `docker-compose.yml`: `documents` and `chunks` tables, a `vector(1024)` column (or your model's dimension), an HNSW index with `vector_cosine_ops`, and the `<=>` operator for search. All SQL uses placeholders.
6. **Embeddings:** a real model, either Voyage AI (`voyage-4`, `input_type="document"` for chunks and `"query"` for questions) or a local sentence-transformers model. Embed in batches. Record the model name per chunk or in config.
7. **Validation and errors:** Pydantic request/response models with sensible limits (question length, `k` between 1 and 20, maximum upload size). LLM errors map to 503/502/504 as in *Serving Claude from FastAPI*; unknown document ids give 404.
8. **Security basics:** an `X-API-Key` header required on every route except `/health`; secrets only in environment variables; `.env` git-ignored with a `.env.example` committed.
9. **Tests** that run with no network, no API keys and no Postgres: fakes for Claude and the embedder, an in-memory store with the same interface as the pgvector one, and `TestClient` for the API.
10. **Deployed** to a public URL, with a README covering setup, the architecture, example requests, your threshold, and a short retrieval evaluation.

## Architecture

```
            ┌────────────────────────── FastAPI app ──────────────────────────┐
 client ──▶ │  /documents ─▶ ingest: clean ─▶ chunk ─▶ embed (batch) ─▶ store │
 (curl,     │                                                          │       │
  web UI)   │  /ask ─▶ embed query ─▶ store.search(k, threshold) ─▶ prompt ─▶ Claude
            │                                   │                       │      │
            │                         nothing relevant? ─▶ "I don't know"     │
            └──────────────────────────────────────────────────────────────────┘
                          │                                   │
                  Postgres + pgvector                Voyage AI / local model
                  (Docker in dev)                    + Claude API
```

The key design rule from this section: **every external thing is a dependency.** The Claude client, the embedder and the store are created in one place and injected with `Depends`, so tests swap them with `app.dependency_overrides`.

## Suggested file layout

```
docs-chat/
├── .env.example              # ANTHROPIC_API_KEY=  VOYAGE_API_KEY=  DATABASE_URL=  APP_API_KEY=
├── .gitignore                # .env, __pycache__/, .venv/
├── docker-compose.yml        # Postgres + pgvector for development
├── README.md
├── pyproject.toml            # or requirements.txt
├── app/
│   ├── main.py               # FastAPI app, routes
│   ├── config.py             # Settings from the environment, get_settings()
│   ├── deps.py               # get_client, get_embedder, get_store, require_api_key
│   ├── models.py             # Pydantic request/response models
│   ├── ingest.py             # clean_text, split_markdown / chunk_words
│   ├── embeddings.py         # VoyageEmbedder (or LocalEmbedder): embed_documents, embed_query
│   ├── store.py              # PgVectorStore (+ schema SQL)
│   └── rag.py                # build_prompt, extract_citations, answer
├── samples/                  # a few public documents to demo with
├── evals/
│   ├── golden.json           # 15-30 questions with relevant chunk ids
│   └── run_eval.py           # prints recall@k and MRR
└── tests/
    ├── fakes.py              # AsyncFake / FakeAnthropic wrapper, fake embedder, MemoryStore
    ├── test_ingest.py
    ├── test_rag.py
    └── test_api.py
```

## Postgres in Docker

`docker-compose.yml` for development:

```yaml
services:
  db:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: docs
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d docs"]
      interval: 5s
      retries: 10

volumes:
  pgdata:
```

`docker compose up -d` starts it; `docker compose down` stops it (the `pgdata` volume keeps your data; `down -v` wipes it). Your `.env` then has `DATABASE_URL=postgresql://app:devpassword@localhost:5432/docs`.

Create the schema at startup (FastAPI's `lifespan`) with `CREATE ... IF NOT EXISTS` statements:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    position     INT NOT NULL,
    heading      TEXT NOT NULL DEFAULT '',
    text         TEXT NOT NULL,
    embedding    vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks (document_id);
```

## Build plan

### Step 1: project skeleton and `/health`

Create the repo, a virtual environment, and install `fastapi[standard]`, `anthropic`, `psycopg[binary]`, `psycopg_pool`, `pgvector`, `numpy`, `python-dotenv`, `pytest`, and your embedding library (`voyageai` or `sentence-transformers`). Write `config.py` with a `Settings` model read from the environment, `main.py` with `GET /health`, and one `TestClient` test. Commit.

### Step 2: ingestion, pure Python

Port your `clean`, `split_markdown` and `chunk_words` from *Chunking documents* into `ingest.py`. Unit-test them on a sample document. No database, no API: this step is fast to test and you'll lean on it.

### Step 3: the store, in memory first

Write `MemoryStore` (the NumPy store from *RAG from scratch*) in `tests/fakes.py`, with an interface you'll keep: `add_document(title, chunks, vectors) -> int`, `search(query_vector, k, min_score) -> list[Hit]`, `list_documents()`, `delete_document(id)`. Then `rag.py` with `build_prompt`, `extract_citations` and `answer(client, embedder, store, question, k, min_score)`. Test `answer` with `FakeAnthropic` and a fake embedder, including the no-hits case making no API call.

### Step 4: Postgres

`docker compose up -d`, then write `PgVectorStore` with the same interface: `register_vector`, inserts inside a transaction, `ORDER BY embedding <=> %s LIMIT %s`, `1 - (embedding <=> %s)` as the score. Use a connection pool (`psycopg_pool.ConnectionPool`, or the async version) created in the lifespan and provided by `get_store`. Try it from a small script before wiring it into the API.

### Step 5: real embeddings

Write the embedder: `embed_documents(texts)` and `embed_query(text)`, with batching (and the retry-with-backoff you wrote in the LLM APIs section). Ingest your samples, then print the top score for ten answerable and ten unanswerable questions to choose your threshold.

### Step 6: the API

Routes for `/documents` (upload, list, delete) and `/ask`, all through dependencies and protected by `require_api_key`. For file uploads, FastAPI's `UploadFile` needs `python-multipart`, which `fastapi[standard]` includes. Map LLM errors to HTTP codes. Test every route with `TestClient` and `app.dependency_overrides` for the client, embedder and store.

### Step 7: evaluation

Write 15–30 golden questions for your sample documents with the relevant chunk ids, and `evals/run_eval.py` to print recall@5 and MRR. Put the numbers in the README. Try one change (chunk size, k, or adding the heading to the embedded text) and record whether it helped.

### Step 8: deploy

Deploying is covered properly in the Shipping section; for now, a basic deploy to a public URL:

- **Database:** create a Postgres database on the platform (Railway and Render both offer one). Run `CREATE EXTENSION vector;` once; if their Postgres doesn't support pgvector, use a hosted Postgres that does (Neon and Supabase both do) and point `DATABASE_URL` at it.
- **App:** connect your GitHub repo. Start command: `fastapi run app/main.py --port $PORT` (or `uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Set `ANTHROPIC_API_KEY`, your embedding key, `DATABASE_URL` and `APP_API_KEY` as environment variables in the dashboard: never commit them.
- Upload your sample documents to the live URL and ask a question with `curl`. Put a working `curl` example in the README.

Use `claude-haiku-5-5` while developing and choose the model for the deployed version deliberately; note the cost per question in the README (input + output tokens × price).

## Testing with fakes

Your test suite must pass with no network and no keys: run `pytest` with Wi-Fi off to check. The pieces:

- **Claude:** the async adapter from *Serving Claude from FastAPI* around a scripted fake (copy the pattern into `tests/fakes.py`).
- **Embeddings:** a deterministic fake like the hashed bag-of-words one you used in the exercises: texts sharing words get similar vectors, so retrieval tests are meaningful.
- **Store:** `MemoryStore` with the same interface as `PgVectorStore`. Optionally, a separate test marked `@pytest.mark.integration` runs against the Docker database.
- **API:** `TestClient(app)` with `app.dependency_overrides[get_client]`, `[get_embedder]`, `[get_store]` and `[get_settings]`.

Must-have tests: chunking edge cases; `/ask` returns cited sources; the no-relevant-chunks path makes zero Claude calls; invented citations are dropped; missing or wrong API key gives 401; a 429 from Claude gives 503; re-uploading a title replaces its chunks.

## Stretch goals

- **Hybrid search:** add Postgres full-text search (`tsvector` + GIN index) and fuse it with vector results using reciprocal rank fusion. Show the before/after recall in the README.
- **Reranking:** retrieve 30 candidates and rerank with Voyage `rerank-3` or Claude Haiku; measure the change.
- **Streaming answers:** `POST /ask/stream` returning server-sent events, with the sources sent as a final event.
- **Retrieval eval in CI:** run the golden set in a GitHub Action and fail if recall@5 drops below a threshold.
- **Conversation:** accept chat history and rewrite follow-ups into standalone queries.
- **PDFs:** extract text with pypdf or PyMuPDF and keep page numbers in the chunk metadata for citations.
- **A tiny web page** served by FastAPI that uploads a file and shows answers with clickable sources.

## Submitting

Paste your GitHub repo URL and your live URL below, and tick each checklist item as you finish it.
