# Embeddings and semantic search

## Why this matters

Keyword search fails the moment a user's words differ from the document's: someone asks "can I get my money back?" and your policy says "refunds are issued within 30 days". **Embeddings** fix this. They turn text into vectors such that texts with similar *meaning* are close together, so you can find the refund policy from a question that never says "refund". Every RAG system, semantic search box, "related articles" widget and duplicate-ticket detector is built on them, and choosing, calling, batching and caching an embedding model are everyday AI engineering tasks.

## 1. What an embedding is

An **embedding model** is a neural network that maps a piece of text to a fixed-length list of numbers, a vector:

```
"Refunds are issued within 30 days"   ──▶  [0.021, -0.113, 0.087, ..., 0.004]   (1024 numbers)
"Can I get my money back?"            ──▶  [0.019, -0.098, 0.091, ..., 0.012]
"The office cat is called Biscuit"    ──▶  [-0.140, 0.032, -0.005, ..., 0.077]
```

The model was trained so that texts which mean similar things get vectors pointing in similar directions. You never interpret the individual numbers; you compare vectors.

How do you compare them? You already know: **cosine similarity**, from *Vectors, the dot product and cosine similarity* in the Maths section.

```
cos(a, b) = (a · b) / (‖a‖ ‖b‖)
```

It's 1 when two vectors point the same way, around 0 when they're unrelated, and negative when they point apart. For text embeddings, related texts typically score well above unrelated ones, but the absolute numbers depend on the model, so you'll calibrate thresholds per model (more on that in *RAG from scratch*).

Some vocabulary:

- **Dimension**: the vector length. Common sizes are 384, 768, 1024, 1536 and 3072. More dimensions can capture more nuance but cost more storage and compute.
- **Embedding space**: all possible vectors from one model. Vectors from *different* models live in different spaces and **cannot be compared**, even if the dimensions match.
- **Dense** versus **sparse**: embeddings are dense (every number used). Keyword methods like BM25, in *Better retrieval*, are sparse (one slot per word, mostly zeros).

## 2. Normalisation: why dot product is enough

If every vector has length 1, the denominator in the cosine formula is 1, and cosine similarity **equals the dot product**. Dividing a vector by its length is called **L2 normalisation**:

```python
import numpy as np

def normalise(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)  # leave all-zero rows as zeros

docs = normalise(np.array([[3.0, 4.0], [1.0, 0.0], [0.0, 2.0]]))
query = normalise(np.array([1.0, 1.0]))
print(docs @ query)  # [0.98994949 0.70710678 0.70710678]: cosine similarity of each row
```

Many hosted models (Voyage AI's included) return vectors that are already normalised. Normalise anyway when you're not sure; it's one line and makes `docs @ query` correct. For unit vectors, cosine similarity and Euclidean distance also produce the same *ranking*, which is why vector databases let you pick either.

## 3. Semantic search is nearest-neighbour search

Semantic search is three steps:

1. **Index time:** embed every document (or chunk) once and store the vectors in a matrix, one row per document.
2. **Query time:** embed the query with the same model.
3. Compute the similarity between the query and every row, and return the top *k*.

You wrote step 3 in the Maths section's top-k exercise. Here it is with an embedding function plugged in:

```python
from fake_embed import embed   # a toy embedder that ships with your exercises

texts = [
    "Refunds are issued within 30 days of purchase.",
    "We ship to Lagos, Abuja and Accra.",
    "Our office is open Monday to Friday, 9am to 5pm.",
]
doc_vecs = embed(texts)                    # shape (3, 256), rows normalised
q = embed(["How many days do I have to get a refund?"])[0]

scores = doc_vecs @ q
order = np.argsort(-scores, kind="stable")[:2]
for i in order:
    print(f"{scores[i]:.2f}  {texts[i]}")
# 0.41  Refunds are issued within 30 days of purchase.
# 0.00  We ship to Lagos, Abuja and Accra.
```

> **Note:** `fake_embed` is a deterministic stand-in for a real model, used so your exercises run offline and for free. It hashes words into 256 slots, so texts that share words are similar. It does **not** understand meaning: "money back" and "refund" score zero with it, whereas a real model scores them highly. Everything else about the code is the same as with a real model.

This brute-force scan (compare against every row) is exact and, with NumPy, fast up to roughly a hundred thousand vectors. Beyond that you use an **approximate nearest neighbour (ANN)** index, which trades a tiny bit of accuracy for huge speed-ups. pgvector's **HNSW** index is one: it builds a layered graph of vectors and walks it towards the query, checking a few hundred candidates instead of millions.

## 4. Choosing an embedding model

Anthropic doesn't offer an embedding model; Claude generates text, it doesn't embed it. You pair Claude with a separate embedding model. Two good routes:

### Hosted: Voyage AI

Anthropic's documentation recommends **Voyage AI** (now part of MongoDB). It's an HTTP API like Claude's, with a Python package:

```python
import voyageai  # pip install voyageai; reads VOYAGE_API_KEY

vo = voyageai.Client()
docs = ["Refunds are issued within 30 days.", "We ship to Lagos, Abuja and Accra."]

doc_vecs = vo.embed(docs, model="voyage-4", input_type="document").embeddings  # list of 1024-float lists
q_vec = vo.embed(["Can I get my money back?"], model="voyage-4", input_type="query").embeddings[0]
```

- The current general-purpose models are `voyage-4-large` (best quality), `voyage-4` (balanced) and `voyage-4-lite` (cheapest, fastest). There are specialised ones for code, law and finance. Their default dimension is **1024**, which is why the pgvector column in this section is `vector(1024)`.
- **`input_type` matters.** Pass `"document"` when embedding your corpus and `"query"` when embedding a user's question. The model prepends a different instruction for each, which improves retrieval. Don't leave it out.
- The vectors come back normalised, so dot product equals cosine similarity.

### Local: open-source models with sentence-transformers

You can also run an open-source model on your own machine or server with the `sentence-transformers` library:

```python
from sentence_transformers import SentenceTransformer  # pip install sentence-transformers

model = SentenceTransformer("all-MiniLM-L6-v2")        # ~90 MB download, 384 dimensions
vecs = model.encode(["Refunds are issued within 30 days."], normalize_embeddings=True)
print(vecs.shape)  # (1, 384)
```

`all-MiniLM-L6-v2` is small and fast enough to run on a laptop CPU; larger open models (BGE, E5, Nomic, Voyage's open-weight `voyage-4-nano`) score better and want more memory or a GPU.

### How to choose

| Consideration | Hosted (Voyage etc.) | Local (sentence-transformers) |
|---|---|---|
| Quality | generally higher | good, varies by model |
| Cost | per token, small | free per call; you pay for the server |
| Setup | an API key | model download, more RAM, maybe a GPU |
| Privacy | text leaves your server | text stays on your machine |
| Latency | a network round trip | depends on your hardware |

Practical defaults: start with a hosted general model for client work; choose local when data can't leave the premises or volume is huge. Public benchmarks like the **MTEB leaderboard** compare models, but the only benchmark that really counts is your own: a few dozen real questions with known answers, which you'll build in *Better retrieval*.

Whatever you pick, **write it down with the vectors** (model name and dimension). If you ever change model, you must re-embed everything: old and new vectors aren't comparable.

## 5. Batching

Embedding APIs accept many texts per request, and one request with 128 texts is much faster than 128 requests with one. Each provider has limits on texts per request and tokens per request (Voyage: up to 1,000 texts, with a total token cap per model), so you split large jobs into batches:

```python
from collections.abc import Callable

import numpy as np


def embed_in_batches(texts: list[str], embed: Callable[[list[str]], np.ndarray],
                     batch_size: int = 128) -> np.ndarray:
    parts = [embed(texts[i:i + batch_size]) for i in range(0, len(texts), batch_size)]
    return np.vstack(parts) if parts else np.empty((0, 0))
```

Passing `embed` in as a function is the same design as passing `client` to your Claude functions: production code passes a wrapper around Voyage, tests pass the fake. For ingesting thousands of documents, combine batching with the concurrency patterns from *Async Python* (a semaphore limiting parallel requests) and the retry-with-backoff you wrote in the LLM APIs section.

## 6. Caching

Embedding the same text twice gives the same vector, so never pay twice. Cases where caching saves real money:

- Re-running ingestion after adding three new files to a folder of three thousand.
- Popular queries ("opening hours", "refund policy") arriving hundreds of times a day.
- Re-chunking experiments where most chunks don't change.

A cache maps text to vector. The key must include everything that affects the vector: the **model name** and the `input_type`, as well as the text. In memory, a dict works; across restarts, store vectors in your database (which RAG does anyway) and look up by a hash of the text:

```python
import hashlib

def cache_key(model: str, input_type: str, text: str) -> str:
    return hashlib.sha256(f"{model}\x00{input_type}\x00{text}".encode()).hexdigest()
```

Hashing keeps keys short and fixed-length even for long chunks. Store the hash in a column with an index, and before embedding a batch, query which hashes already exist.

> **Try it:** In the cache exercise, wrap `fake_embed.embed` with a function that prints each batch it receives, then call your cache twice with overlapping lists and watch only the new texts get embedded.

## 7. Cost

Embeddings are cheap compared to generation, but not free, and the bill scales with your corpus. Price them like Claude calls, per million input tokens (there are no output tokens). Check the provider's pricing page for current numbers, then estimate:

```
corpus tokens ≈ words × 1.3
one-off cost  = corpus tokens / 1,000,000 × price per 1M tokens
```

A 500-page manual is about 250,000 words, roughly 325,000 tokens: pennies to embed once. The real costs are re-embedding everything after a model change, and embedding at query time on high traffic. Caching handles the second; the first is a reason to pick a model carefully up front. Storage is the other cost: 1024 float32 numbers is 4 KB per chunk, so a million chunks is about 4 GB before indexes. Smaller dimensions (Voyage supports 256 and 512) or quantised vectors cut that.

## Common mistakes

- **Comparing vectors from different models**, or from the same model with different dimensions. The numbers will be meaningless, and nothing will error.
- **Forgetting `input_type`** (query vs document) with models that support it.
- **Using dot product on unnormalised vectors** and calling it cosine similarity.
- **Embedding one text per request** in a loop. Batch.
- **Caching by text alone** and then switching models: old vectors come back for the new model. Put the model in the key.
- **Treating a similarity score as a probability.** 0.6 doesn't mean "60% relevant"; thresholds must be calibrated per model.
- **Embedding whole documents.** A 30-page PDF squeezed into one vector loses detail. Split it first: that's the next lesson.

## Recap

- An embedding model maps text to a fixed-length vector so that similar meanings point in similar directions.
- Compare with cosine similarity; for normalised vectors that's just the dot product, so `matrix @ query` scores everything at once.
- Semantic search = embed the corpus once, embed the query, take the top-k nearest. ANN indexes like HNSW make it fast at scale.
- Anthropic has no embedding model: use Voyage AI (`voyage-4`, 1024 dimensions, `input_type="document"`/`"query"`) or a local sentence-transformers model.
- Batch requests, cache by (model, input type, text), and record which model produced each vector.
