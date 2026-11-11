# RAG from scratch

## Why this matters

Claude knows a lot, but nothing about your client's refund policy, last week's meeting notes or their internal API. **Retrieval-augmented generation (RAG)** fixes that without training anything: at question time you find the few passages that matter and hand them to the model with the question. "An AI assistant that answers questions from our documents" is the most requested AI feature in business, and under the frameworks every implementation is the same short pipeline. You've built each piece in the last three lessons; now you'll connect them, with citations and an honest "I don't know".

## 1. The pipeline

RAG has two phases.

**Ingestion** (once per document, ahead of time):

```
document ──▶ extract + clean ──▶ chunk ──▶ embed each chunk ──▶ store (text, metadata, vector)
```

**Query** (every question):

```
question ──▶ embed ──▶ retrieve top-k similar chunks ──▶ build prompt ──▶ Claude ──▶ answer + citations
                                │
                                └── nothing similar enough? ──▶ "I don't know" (no LLM call)
```

Why not just paste all the documents into the prompt? For a handful of short documents, you can, and should: it's simpler and works well. RAG earns its place when the corpus is bigger than you'd want to send on every question (cost and latency grow with every token), when it changes often, or when you need to show which passage an answer came from.

## 2. Ingest: chunk, embed, store

You'll represent each chunk as a dict with an `id`, `source` and `text` (plus any other metadata from *Chunking documents*). The store keeps the chunks in a list and their normalised vectors in a NumPy matrix, one row per chunk:

```python
import numpy as np


def normalise(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


class VectorStore:
    def __init__(self, embed):
        self.embed = embed                  # embed(list[str]) -> array, one row per text
        self.chunks: list[dict] = []
        self.vectors: np.ndarray | None = None

    def add(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        vecs = normalise(np.asarray(self.embed([c["text"] for c in chunks]), dtype=float))
        self.vectors = vecs if self.vectors is None else np.vstack([self.vectors, vecs])
        self.chunks.extend(chunks)
```

Ingesting a folder of Markdown files with the chunker from the previous lesson:

```python
from pathlib import Path

store = VectorStore(embed)
for path in Path("docs").glob("*.md"):
    pieces = split_markdown(path.read_text(), source=path.name, max_words=200)
    store.add([{"id": f"{c.source}#{c.position}", "source": c.source,
                "heading": c.heading, "text": c.text} for c in pieces])
```

Ids like `policy.md#3` are stable (the same chunk gets the same id next time), readable in citations, and tell you exactly where to look.

## 3. Retrieve top-k

Retrieval is the semantic search from *Embeddings and semantic search*: embed the question, score every chunk with one matrix-vector product, take the best *k*.

```python
    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[tuple[dict, float]]:
        if self.vectors is None or k <= 0:
            return []
        q = normalise(np.asarray(self.embed([query]), dtype=float))[0]
        scores = self.vectors @ q
        hits = []
        for i in np.argsort(-scores, kind="stable")[:k]:
            if min_score is not None and scores[i] < min_score:
                break  # sorted, so everything after is lower too
            hits.append((self.chunks[i], float(scores[i])))
        return hits
```

Choosing **k**: 3–8 is typical. Too few and the answer may be in chunk 4; too many and you pay for, and distract the model with, irrelevant text.

### The similarity threshold

Top-k *always* returns k results, even when none is relevant. Ask a store full of HR policies "what's the capital of Peru?" and you still get three chunks back, with low scores. Pass those to Claude and it will either answer from its own knowledge (not from your documents, which may be exactly what your client doesn't want) or try to connect irrelevant text to the question.

So add a **minimum score**. If no chunk reaches it, answer "I don't know" yourself, without calling Claude at all: honest, instant, free.

The right threshold depends on the embedding model: scores from different models aren't on the same scale. Calibrate it: run 20 questions your documents *can* answer and 20 they *can't*, print the top score for each, and pick a value that separates the two groups. Re-check whenever you change the model or the chunking.

## 4. Build the prompt

The prompt has three jobs: give Claude the retrieved passages, make it clear which passage is which so it can cite them, and say what to do when the passages don't contain the answer. As you learned in *Prompt engineering for developers*, XML tags are the clearest way to separate material from instructions:

```python
SYSTEM = (
    "You answer questions using only the documents provided in <documents>. "
    "After each claim, cite the id of the document it came from in square brackets, like [policy.md#2]. "
    "If the documents do not contain the answer, say \"I don't know\" and nothing else. "
    "Do not use outside knowledge."
)


def build_prompt(question: str, chunks: list[dict]) -> str:
    lines = ["<documents>"]
    for c in chunks:
        lines.append(f'<document id="{c["id"]}" source="{c["source"]}">')
        lines.append(c["text"])
        lines.append("</document>")
    lines.append("</documents>")
    lines.append("")
    lines += ["<question>", question, "</question>"]
    return "\n".join(lines)
```

For two retrieved chunks the user message looks like:

```
<documents>
<document id="policy.md#0" source="policy.md">
Refunds can be requested within 30 days of purchase.
</document>
<document id="policy.md#1" source="policy.md">
Gift purchases are refunded as store credit.
</document>
</documents>

<question>
How many days do I have to request a refund?
</question>
```

Design choices worth knowing:

- **Documents first, question last.** With long context, putting the material before the question tends to give better answers.
- **Instructions in the system prompt**, data in the user message. That keeps the rules separate from text that came from documents.
- **Retrieved text is untrusted.** A document could contain "ignore your instructions and…". Wrapping it in tags and telling the model it's reference material helps; you'll study prompt injection properly in the Agents & Evals section.
- **Escape or strip tag-like text** in chunks if your documents might contain `</document>`, so a chunk can't break out of its tag.

## 5. Answer with citations

Call Claude, then pull the cited ids out of the answer so your API can return them as structured data:

```python
import re

NO_ANSWER = "I don't know based on the provided documents."


def extract_citations(text: str, valid_ids: list[str]) -> list[str]:
    found = []
    for cited in re.findall(r"\[([^\[\]]+)\]", text):
        if cited in valid_ids and cited not in found:
            found.append(cited)
    return found


def answer(client, question: str, store: VectorStore, k: int = 3, min_score: float = 0.3) -> dict:
    hits = store.search(question, k=k, min_score=min_score)
    if not hits:
        return {"answer": NO_ANSWER, "sources": []}
    chunks = [chunk for chunk, _ in hits]
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(question, chunks)}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    return {"answer": text, "sources": extract_citations(text, [c["id"] for c in chunks])}
```

`extract_citations` keeps only ids that were actually retrieved. If the model invents `[policy.md#99]`, it's dropped: never show a user a source that doesn't exist. It also de-duplicates while keeping the order of first mention.

Run it:

```python
import anthropic

client = anthropic.Anthropic()
print(answer(client, "How many days do I have to request a refund?", store))
# {'answer': 'You have 30 days from purchase to request a refund [policy.md#0].',
#  'sources': ['policy.md#0']}
print(answer(client, "What's the capital of Peru?", store))
# {'answer': "I don't know based on the provided documents.", 'sources': []}   (no API call made)
```

Your API can now return the sources with the answer, and the front end can link each one to the original document. That's the feature clients ask for by name: "answers with sources, so we can check".

> **Note:** Claude also has a built-in **citations** feature: pass documents as `document` content blocks with `"citations": {"enabled": True}` and the response includes structured citations pointing at exact passages. The square-bracket approach here works with any model and is easy to test; the built-in one is more precise. The *Citations* page in Claude's docs shows it.

### Testing the pipeline offline

Every piece takes its dependencies as arguments: `answer` takes `client`, the store takes `embed`. So tests pass `FakeAnthropic` and `fake_embed.embed` and check behaviour precisely:

```python
from fake_embed import embed
from fake_llm import FakeAnthropic, reply, text

store = VectorStore(embed)
store.add([{"id": "policy.md#0", "source": "policy.md",
            "text": "Refunds can be requested within 30 days of purchase."}])

client = FakeAnthropic([reply(text("Within 30 days [policy.md#0]."))])
result = answer(client, "How many days do I have to request a refund?", store)
assert result["sources"] == ["policy.md#0"]
assert "<document id=\"policy.md#0\"" in client.calls[0]["messages"][0]["content"]

client = FakeAnthropic([])  # no scripted replies: any call would fail the test
assert answer(client, "What is the capital of Peru?", store)["sources"] == []
```

## 6. The same store in Postgres with pgvector

The NumPy store lives in memory and vanishes when the process stops. In production the chunks and vectors live in Postgres, with pgvector doing the similarity search. The schema from *SQL and Postgres*:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id         TEXT PRIMARY KEY,                 -- e.g. 'policy.md#0'
    source     TEXT NOT NULL,
    heading    TEXT NOT NULL DEFAULT '',
    text       TEXT NOT NULL,
    embedding  vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
```

pgvector's operators: `<=>` is **cosine distance** (`1 − cosine similarity`), `<->` is Euclidean distance, `<#>` is negative inner product. Sorting by `<=>` ascending gives most-similar first, and the HNSW index built with `vector_cosine_ops` speeds up exactly that ordering.

A pgvector version of the store with psycopg (install `psycopg[binary]` and `pgvector`):

```python
import numpy as np
import psycopg
from pgvector.psycopg import register_vector  # pip install pgvector


class PgVectorStore:
    def __init__(self, conn: psycopg.Connection, embed):
        self.conn, self.embed = conn, embed
        register_vector(conn)  # lets psycopg send and receive numpy arrays as vectors

    def add(self, chunks: list[dict]) -> None:
        vecs = self.embed([c["text"] for c in chunks])
        with self.conn.transaction():
            for c, v in zip(chunks, vecs):
                self.conn.execute(
                    """INSERT INTO chunks (id, source, heading, text, embedding)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, embedding = EXCLUDED.embedding""",
                    (c["id"], c["source"], c.get("heading", ""), c["text"], np.asarray(v)),
                )

    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[tuple[dict, float]]:
        q = np.asarray(self.embed([query])[0])
        rows = self.conn.execute(
            """SELECT id, source, heading, text, 1 - (embedding <=> %s) AS score
               FROM chunks
               ORDER BY embedding <=> %s
               LIMIT %s""",
            (q, q, k),
        ).fetchall()
        hits = [({"id": r[0], "source": r[1], "heading": r[2], "text": r[3]}, float(r[4])) for r in rows]
        return [h for h in hits if min_score is None or h[1] >= min_score]
```

It has the same `add` / `search` interface as the NumPy store, so `answer()` works unchanged with either. That's the payoff of the design: develop and test with the in-memory version, deploy with Postgres. Notes:

- `ON CONFLICT ... DO UPDATE` makes re-ingesting a document an update instead of a duplicate-key error ("upsert").
- With a real embedding model you'd embed queries with `input_type="query"` and chunks with `input_type="document"`, so `embed` becomes two functions, or takes a parameter.
- HNSW is *approximate*. On small tables Postgres may skip the index and scan exactly, which is fine. `SET hnsw.ef_search = 100` trades speed for recall on large ones.

## 7. Watch it explained

Now that you've built your own, the companion video walks through the same ideas (and more advanced variants) using a framework. You'll recognise every step: watch after you've built your own.

## Common mistakes

- **No threshold**, so off-topic questions get confident answers built from irrelevant chunks.
- **A threshold copied from a tutorial** using a different embedding model. Calibrate on your own questions.
- **Not telling the model what to do when the answer is missing.** Without "say I don't know", it fills gaps from general knowledge.
- **Trusting citations blindly.** Keep only ids you actually retrieved.
- **Instructions mixed into the document text** instead of the system prompt, or documents not clearly delimited.
- **Embedding queries and documents with different models**, or re-chunking without re-embedding.
- **Testing only against the real API.** Inject the client and the embedder so the whole pipeline runs offline in tests.

## Recap

- RAG = ingest (chunk → embed → store) once, then per question: embed → retrieve top-k → prompt → answer.
- The store keeps chunks plus a matrix of normalised vectors; search is `vectors @ query`, sorted, top-k.
- A calibrated similarity threshold lets you say "I don't know" without calling the model.
- Put retrieved chunks in `<document id=... source=...>` tags before the question; instruct the model to cite ids and to admit when the answer isn't there.
- Extract citations from the answer and keep only retrieved ids.
- pgvector stores the same data in Postgres: `vector(1024)` column, `<=>` cosine distance, HNSW index, and the same `add`/`search` interface.
