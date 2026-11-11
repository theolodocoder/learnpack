# Better retrieval

## Why this matters

When a RAG app gives a wrong answer, the cause is usually retrieval, not the model: the right chunk never made it into the prompt. Basic vector search misses exact terms (product codes, names, error messages), mixes in documents the user shouldn't see, and struggles with vague or conversational questions. The techniques in this lesson are what separate a demo from a system a client trusts. Above all, you need a way to **measure** retrieval, so you improve it with numbers instead of hunches.

## 1. Measure first: a golden set, recall@k and MRR

Before changing anything, build a **golden set**: 20–50 realistic questions, each labelled with the chunk ids that contain the answer.

```python
golden = [
    {"question": "How long do I have to return an item?", "relevant": ["policy.md#0"]},
    {"question": "Do you deliver to Accra?",              "relevant": ["shipping.md#0"]},
    {"question": "What happens to gift refunds?",         "relevant": ["policy.md#1", "policy.md#4"]},
]
```

Write the questions the way users actually ask them (ask the client for real ones, or check support emails), not by copying sentences from the documents. Include a few that the documents can't answer, so you can tune the "I don't know" threshold too.

Two metrics answer "is retrieval finding the right chunks?":

**Recall@k**: of the relevant chunks, what fraction appear in the top k results?

```
recall@k = |relevant ∩ top-k retrieved| / |relevant|
```

If a question has two relevant chunks and one appears in the top 5, recall@5 = 0.5. For RAG this is the metric that matters most: a chunk that isn't retrieved can't help the answer.

**Reciprocal rank**: 1 divided by the position of the *first* relevant result (1 if it's first, ½ if second, ⅓ if third), or 0 if none is retrieved. Averaged over the golden set, it's the **mean reciprocal rank (MRR)**. It rewards putting a good chunk near the top.

```python
def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & set(relevant)) / len(set(relevant))


def reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float:
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in relevant:
            return 1 / rank
    return 0.0


print(recall_at_k(["a", "x", "b"], ["a", "b", "c"], k=2))   # 0.333...: only "a" is in the top 2
print(reciprocal_rank(["x", "y", "a"], ["a"]))               # 0.333...: first hit at rank 3
```

Run every question, average each metric, and you have two numbers to compare chunking settings, embedding models, k, and every technique below. Keep the golden set in your repo and re-run it whenever you change retrieval: it's a regression test for search quality. (Evaluating the *answers*, not just retrieval, comes in the Agents & Evals section.)

## 2. Metadata filtering

Often the right answer depends on context the query doesn't contain: which customer is asking, which product they use, which documents they're allowed to see. **Filter by metadata before ranking**:

```python
import numpy as np


def search_filtered(store, query: str, k: int, where: dict) -> list[tuple[dict, float]]:
    mask = np.array([all(c.get(key) == value for key, value in where.items()) for c in store.chunks])
    if not mask.any():
        return []
    q = normalise(np.asarray(store.embed([query]), dtype=float))[0]   # normalise() from RAG from scratch
    scores = np.where(mask, store.vectors @ q, -np.inf)    # excluded chunks can never win
    order = np.argsort(-scores, kind="stable")[: min(k, int(mask.sum()))]
    return [(store.chunks[i], float(scores[i])) for i in order]


search_filtered(store, "refund window", k=3, where={"source": "policy.md"})
```

In Postgres it's an ordinary `WHERE` next to the vector ordering:

```sql
SELECT id, text, 1 - (embedding <=> %s) AS score
FROM chunks
WHERE tenant_id = %s AND doc_type = 'policy'
ORDER BY embedding <=> %s
LIMIT 5;
```

Filtering is also **access control**. In a multi-customer app, every query must filter on the customer's id: never rely on the prompt to keep one customer's documents from another. Add an index on columns you filter by often.

## 3. Keyword search and BM25

Embeddings capture meaning but are weak on exact tokens: an order number `INV-20931`, a person's name, an error code `ERR_SSL_PROTOCOL`, a rare product name. Classic **keyword search** is strong exactly there. The standard scoring function is **BM25**. Its intuition:

- A chunk scores higher the more often it contains the query's terms (**term frequency**)…
- …but with diminishing returns: the tenth "refund" adds much less than the first (controlled by `k1`, usually 1.2–2).
- Rare terms count more than common ones (**inverse document frequency**): matching "Biscuit" is more informative than matching "office".
- Long chunks are penalised a little, so they don't win just by containing more words (controlled by `b`, usually 0.75).

For each query term t and chunk d:

```
score(t, d) = idf(t) · tf · (k1 + 1) / (tf + k1 · (1 − b + b · len(d) / avg_len))
idf(t)      = ln(1 + (N − n_t + 0.5) / (n_t + 0.5))
```

where `tf` is how often t appears in d, `N` is the number of chunks, and `n_t` is how many contain t. A chunk's score is the sum over the query's terms. In Python:

```python
import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75):
        self.docs = [Counter(tokenize(t)) for t in texts]
        self.lens = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lens) / len(self.lens) if self.lens else 0.0
        self.k1, self.b, n = k1, b, len(texts)
        df = Counter(term for d in self.docs for term in d)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, query: str) -> list[float]:
        out = []
        for d, length in zip(self.docs, self.lens):
            s = 0.0
            for t in tokenize(query):
                tf = d.get(t, 0)
                if tf:
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / self.avg))
            out.append(s)
        return out


bm25 = BM25(["Invoice INV-20931 was paid in March.", "Refunds take 30 days.", "Invoices are sent monthly."])
print([round(s, 2) for s in bm25.scores("status of inv-20931")])  # [1.66, 0.0, 0.0]: exact token match wins
```

This is fine for thousands of chunks. For more, use a search engine. **Postgres has full-text search built in**: a `tsvector` column (the processed words of the text), a GIN index, and `ts_rank` for scoring:

```sql
ALTER TABLE chunks ADD COLUMN tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', text)) STORED;
CREATE INDEX chunks_tsv_idx ON chunks USING gin (tsv);

SELECT id, ts_rank(tsv, query) AS score
FROM chunks, websearch_to_tsquery('english', 'refund gift card') AS query
WHERE tsv @@ query
ORDER BY score DESC
LIMIT 10;
```

`to_tsvector('english', ...)` lowercases, drops stopwords and stems words ("refunds" → "refund"), and `websearch_to_tsquery` parses a user's query safely. `ts_rank` isn't exactly BM25, but it plays the same role.

## 4. Hybrid search with reciprocal rank fusion

Vector search and keyword search fail in different places, so run **both** and combine the results. The problem: their scores aren't comparable. Cosine similarity is between −1 and 1; BM25 scores are unbounded and depend on the corpus. Adding them is meaningless.

**Reciprocal rank fusion (RRF)** sidesteps this by ignoring scores and using only **ranks**. Each list gives every document `1 / (k + rank)`, with ranks starting at 1, and a document's fused score is the sum over all lists it appears in:

```
RRF(d) = Σ over lists  1 / (k + rank_of_d_in_that_list)        (k = 60 by convention)
```

```
vector:  [A, B, C]        keyword: [C, A, D]
A: 1/61 + 1/62 = 0.03252
C: 1/63 + 1/61 = 0.03227
B: 1/62        = 0.01613
D: 1/63        = 0.01587
fused:   [A, C, B, D]
```

Documents ranked well by *both* methods rise to the top; a document found by only one method still appears. The constant `k = 60` dampens the difference between rank 1 and rank 2, so no single list dominates. You'll implement RRF in the exercise.

In practice: retrieve, say, the top 20 from each method, fuse, and keep the top 5. Postgres can do both searches in one query with two CTEs (`WITH vector_hits AS (...), keyword_hits AS (...)`) and a `FULL OUTER JOIN`, which keeps hybrid search inside the database you already have.

## 5. Reranking

Embedding search is fast because the query and each chunk are embedded **separately** (a "bi-encoder"). A **reranker** reads the query and a chunk **together** and outputs a relevance score. That's far more accurate, but too slow to run on every chunk. So you combine them:

```
retrieve top 30 cheaply (vector / hybrid)  ──▶  rerank those 30 accurately  ──▶  keep top 5 for the prompt
```

Two ways to rerank:

**A dedicated rerank model.** Voyage AI offers `rerank-3` and the cheaper `rerank-3-lite`:

```python
import voyageai

vo = voyageai.Client()
result = vo.rerank(query, [c["text"] for c in candidates], model="rerank-3", top_k=5)
reranked = [candidates[r.index] for r in result.results]   # each r also has .relevance_score
```

Open-source "cross-encoder" models (via sentence-transformers' `CrossEncoder`) run locally.

**Claude as the reranker.** Send the question and numbered candidates and ask for the relevant ones in order, using structured output from *Structured output with Pydantic*:

```python
from pydantic import BaseModel


class Ranking(BaseModel):
    relevant_ids: list[str]  # most relevant first; leave out irrelevant ones


def llm_rerank(client, question: str, candidates: list[dict], top_n: int = 5) -> list[dict]:
    docs = "\n".join(f'<document id="{c["id"]}">\n{c["text"]}\n</document>' for c in candidates)
    response = client.messages.parse(
        model="claude-haiku-5-5", max_tokens=1000,
        messages=[{"role": "user", "content":
                   f"<documents>\n{docs}\n</documents>\n\n<question>{question}</question>\n\n"
                   "List the ids of documents that help answer the question, most relevant first."}],
        output_format=Ranking,
    )
    by_id = {c["id"]: c for c in candidates}
    return [by_id[i] for i in response.parsed_output.relevant_ids if i in by_id][:top_n]
```

A cheap model like Haiku is plenty for this. The LLM reranker can also *drop* irrelevant chunks entirely, which helps the "I don't know" case. The cost is an extra model call (latency and money) on every question, so measure whether the gain in recall is worth it.

## 6. Query rewriting

Users write queries badly for search: "and what about for gifts?" (depends on chat history), "it's not working!!", or one question containing three. A cheap LLM call before retrieval can fix that:

- **Standalone rewriting** for chat: turn the latest message plus history into a self-contained query. "And what about for gifts?" after a refund question becomes "What is the refund policy for gift purchases?". This is the most valuable rewrite in conversational RAG.
- **Multi-query**: generate 3–4 phrasings, retrieve for each, and fuse the lists with RRF. This improves recall when vocabulary varies.
- **Decomposition**: split "compare the refund policies for gifts and for sale items" into two queries.
- **HyDE** (hypothetical document embeddings): ask the model to write a plausible *answer*, and embed that instead of the question, since an answer looks more like a document than a question does.

```python
def standalone_query(client, history: list[dict], question: str) -> str:
    transcript = "\n".join(f'{m["role"]}: {m["content"]}' for m in history[-6:])
    response = client.messages.create(
        model="claude-haiku-5-5", max_tokens=200,
        system="Rewrite the user's last question as one standalone search query. Reply with the query only.",
        messages=[{"role": "user", "content": f"<history>\n{transcript}\n</history>\n\n<question>{question}</question>"}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()
```

Each rewrite adds latency and cost, and a bad rewrite can make things worse. Only keep the ones your golden set says help.

> **Try it:** After the RRF exercise, fuse the rankings for two phrasings of the same question from your vector store, and compare the result to each list alone.

## 7. A sensible order of improvements

When retrieval is weak, work through these roughly in order, measuring recall@k and MRR after each:

1. **Look at failures.** Print the retrieved chunks for the questions that fail. Often the cause is obvious: bad PDF extraction, chunks too big or small, missing headings.
2. **Fix chunking and cleaning.** Cheapest and often the biggest win.
3. **Add metadata filters** where the context is known (user, product, document type).
4. **Add keyword search with RRF** if users search for codes, names or jargon.
5. **Add a reranker** when the right chunk is often retrieved but ranked below the cut-off.
6. **Rewrite queries** for chat and vague queries.
7. **Try a better embedding model**, and re-embed everything.

## Common mistakes

- **Tuning without a golden set.** Three hand-picked questions that "look better" prove nothing.
- **Golden questions copied from the documents' wording**, which makes vector *and* keyword search look perfect.
- **Adding raw scores from different retrievers.** Fuse ranks (RRF), not scores.
- **Relying on the prompt for access control** instead of filtering by tenant or user.
- **Reranking only the top 5.** A reranker can only reorder what it's given; retrieve more candidates (20–50) first.
- **Stacking every technique at once** and not knowing which helped. Change one thing, measure, keep or revert.

## Recap

- Measure retrieval with a golden set: recall@k (did the relevant chunks make the top k?) and MRR (how high was the first one?).
- Metadata filtering narrows the search by known context and enforces access control; in Postgres it's a `WHERE` clause.
- BM25 keyword search catches exact terms embeddings miss; Postgres full-text search (`tsvector`, GIN, `ts_rank`) gives you this in the database.
- Hybrid search fuses vector and keyword rankings with reciprocal rank fusion: `Σ 1/(60 + rank)`.
- Rerankers (Voyage `rerank-3`, cross-encoders, or Claude) reorder a larger candidate set accurately.
- Query rewriting (standalone, multi-query, decomposition, HyDE) fixes badly phrased questions; keep only what the numbers support.
