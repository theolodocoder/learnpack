# Internships and junior AI engineer interviews

## Why this matters

Gigs build your track record; an internship or junior role builds your career fastest, because you work next to experienced engineers on systems bigger than you could build alone. As a CS student you're in the best position you'll ever be in for internships: companies expect students to apply, and AI startups especially want people who've actually shipped LLM features. The interview loop for these roles is different from classic big-tech loops. It's usually less about algorithm puzzles and more about whether you can write practical Python, explain your projects and design an LLM system sensibly. This lesson prepares you for each round.

## 1. Where to find internships and junior roles

- **Startup job boards**: Y Combinator's job board and Work at a Startup, and Wellfound list roles at early-stage companies, many of them remote and many building with LLMs.
- **Company career pages**: make a list of 30–50 AI startups whose products you've used or admired, and check their careers pages monthly. Many post internships only there.
- **LinkedIn**: set job alerts for "AI engineer intern", "ML engineer intern", "LLM engineer", "AI engineer junior", "applied AI". Also watch posts from founders saying "we're hiring".
- **X**: founders and engineers often tweet roles before posting them anywhere. Your build-in-public network helps here.
- **Local and pan-African tech companies**: fintechs, health-tech and logistics companies in Nigeria and across Africa are adding AI features and hiring for them.
- **Your university**: career services, lecturers' industry contacts, alumni at tech companies.
- **Referrals**: by far the highest response rate. A short, specific message to an engineer at the company ("I built X with your API; I'm applying for the intern role; would you be open to referring me?") works more often than you'd expect.

Apply steadily: a target like **10 applications a week**, each with a tailored first paragraph, is more effective than 100 in one weekend.

## 2. A resume that shows shipped projects

For a student, the projects section **is** the resume. Put it above work experience if your experience is unrelated (your marketing experience still goes on: it shows communication and business sense).

One page. Structure:

1. Name, email, GitHub, portfolio site, LinkedIn, location / time zone
2. **Projects** (3–4, most impressive first)
3. Experience (freelance clients count; so does marketing work)
4. Education
5. Skills (short: Python, FastAPI, PostgreSQL/pgvector, Docker, Claude API, evals, tracing)

Each project gets a title, a one-line description, links, and 2–3 bullets in this shape:

```
[Action verb] [what you built] [how / key technical choice], [result with a number].
```

Example:

```
DocPilot: chat with company documents  ·  github.com/ada-obi/docpilot  ·  docpilot.example.com
- Built a RAG API (FastAPI, Postgres + pgvector, Claude) that answers from 40 policy PDFs with page citations.
- Added hybrid search with reciprocal rank fusion, raising retrieval hit rate @5 from 0.78 to 0.93 on a 60-question eval set.
- Dockerised and deployed with request tracing; ~$0.002 per answer, 1.8 s median latency, used by 12 staff for 3 weeks.
```

Every bullet is a thing the interviewer can ask you about. Make sure you can talk about each for five minutes.

## 3. The interview loop

A typical loop for an AI engineering intern or junior role at a startup:

| Round | What they check | Length |
|---|---|---|
| Recruiter / founder screen | Motivation, communication, logistics (time zone, visa, start date) | 15–30 min |
| Python live coding | Practical code: parse data, use dicts and classes, handle edge cases, talk while coding | 45–60 min |
| Project deep-dive | Do you really understand what you built? Trade-offs, failures, what you'd change | 45–60 min |
| LLM / RAG system design | Can you design an LLM feature end to end, including evals and cost? | 45–60 min |
| Behavioural | Ownership, learning, handling feedback and ambiguity | 30–45 min |

Some companies replace live coding with a take-home task (often "build a small LLM feature"). Treat it like a client project: tests, a README with results, and a short note on trade-offs.

## 4. Python live coding (practical, not puzzles)

Startup coding rounds tend to look like real work: process a log, count things, build a small cache, merge time ranges. They test whether you write clear, correct Python and handle edge cases, not whether you've memorised dynamic programming.

How to run the round:

1. **Restate the problem and ask questions.** "Can the input be empty? Are timestamps sorted? What should happen with malformed lines?"
2. **Walk through one example by hand** before coding.
3. **Write the simple correct version first**, talking as you go.
4. **Test it yourself** with the example and one edge case.
5. **Then discuss improvements**: complexity, memory, what you'd do with 10 GB of input.

### Example: parsing a log

> Given log lines like `2026-11-12T09:15:02 INFO /api/chat 200 812ms`, return the 95th-percentile latency per endpoint and the error rate (status ≥ 500).

```python
from collections import defaultdict

def summarise(lines: list[str]) -> dict[str, dict[str, float]]:
    latencies: dict[str, list[int]] = defaultdict(list)
    errors: dict[str, int] = defaultdict(int)
    for line in lines:
        parts = line.split()
        if len(parts) != 5:
            continue                      # skip malformed lines rather than crash
        _, _, path, status, ms = parts
        latencies[path].append(int(ms.removesuffix("ms")))
        errors[path] += int(status) >= 500
    out = {}
    for path, values in latencies.items():
        values.sort()
        p95 = values[min(len(values) - 1, int(0.95 * len(values)))]
        out[path] = {"p95_ms": p95, "error_rate": errors[path] / len(values)}
    return out

logs = [
    "2026-11-12T09:15:02 INFO /api/chat 200 812ms",
    "2026-11-12T09:15:03 INFO /api/chat 200 640ms",
    "2026-11-12T09:15:04 ERROR /api/chat 503 30000ms",
    "2026-11-12T09:15:05 INFO /api/upload 200 1200ms",
    "garbage line",
]
print(summarise(logs))
# {'/api/chat': {'p95_ms': 30000, 'error_rate': 0.3333333333333333}, '/api/upload': {'p95_ms': 1200, 'error_rate': 0.0}}
```

Things worth saying out loud: you skip malformed lines (and would count them in production), `defaultdict` avoids key checks, and for huge files you'd stream lines rather than load a list.

### Example: a rate-limit counter

> Allow at most `limit` requests per user in any rolling `window` seconds.

```python
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, user: str, now: float) -> bool:
        q = self.hits[user]
        while q and q[0] <= now - self.window:   # drop timestamps outside the window
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

rl = RateLimiter(limit=2, window=10)
print([rl.allow("ada", t) for t in (0, 1, 2, 11, 12)])
# [True, True, False, True, True]
```

Passing `now` in, rather than calling `time.time()` inside, makes it testable: a point interviewers like. Follow-ups you might get: memory per user (bounded by `limit`), and what changes with many servers (store counters in Redis).

The two practice exercises for this lesson are classics of the same style: an **LRU cache** with `OrderedDict`, and **merging overlapping time slots**.

> **Note:** LeetCode-style data-structures-and-algorithms rounds are common at big tech companies and some larger firms. If you target those, work through **NeetCode 150** later, 2–3 problems a day. For most AI startup internships, practical Python like the above plus strong project knowledge matters more.

## 5. The project deep-dive

The interviewer picks one of your projects (usually the one you're proudest of) and digs. Prepare a 3-minute overview for each project:

1. **Problem and user**: who it's for and why it matters.
2. **Architecture**: the main components and data flow.
3. **One hard problem** and how you solved it.
4. **Results**: your eval numbers, cost, latency, users.
5. **What you'd do differently** or next.

Then prepare for the follow-ups. Good interviewers ask "why?" until you reach the edge of what you know:

- "Why chunks of 500 tokens? What happens at 100 or 2,000?"
- "How do you know your eval set represents real usage?"
- "What's your LLM judge's agreement with a human?"
- "What happens if the Claude API is down?"
- "How would this handle 100× the documents?"
- "Where does the latency go?"

It's fine to say "I didn't measure that; here's how I would." That's a strong answer. Making something up is a weak one, and experienced interviewers can tell.

## 6. LLM / RAG system design: a whiteboard walkthrough

The most common AI system-design prompt is some version of: **"Design a system that lets employees ask questions about the company's internal documents."** Here's a walkthrough the way you'd do it on a whiteboard, in about 40 minutes.

### Step 1: requirements (5 min)

Ask, then write down what you agreed:

```
Functional
- Employees ask questions in a web chat; answers cite source documents
- Sources: ~50k docs (PDF, DOCX, Confluence pages), ~2M chunks; 500 new/changed docs per day
- Respect permissions: users only see answers from docs they can access

Non-functional
- 2,000 employees, peak ~20 questions/second
- First token in < 2 s, full answer in < 8 s
- Accuracy target: ≥ 85% correct on an agreed eval set; prefer "I don't know" over a wrong answer
- Budget: a few thousand dollars a month all-in
```

Permissions and freshness are the two requirements candidates most often forget. Raise them yourself.

### Step 2: high-level components (5 min)

```
              ┌─────────────── INGESTION (async) ───────────────┐
 sources ──►  │ connectors → parse → chunk → embed → index      │
 (S3, wiki)   │ (+ doc ACLs, hash for change detection)         │
              └──────────────────────┬──────────────────────────┘
                                     ▼
                     ┌──────────────────────────────┐
                     │ Postgres + pgvector          │
                     │ chunks, embeddings, metadata,│
                     │ ACL groups, full-text index  │
                     └──────────────┬───────────────┘
                                    │
 user ─► API gateway ─► query service ─► retrieve (vector + keyword, ACL filter)
         (auth, rate limit)     │        → rerank → top-k chunks
                                │        → prompt (question + chunks + rules)
                                │        → Claude (streamed) → answer + citations
                                ▼
                    tracing, logs, feedback (👍/👎), eval jobs
```

### Step 3: data flow in detail (10 min)

**Ingestion** (offline, a queue of jobs):

1. Connectors pull new or changed documents; a content hash skips unchanged ones.
2. Parse to text, keeping structure (headings, page numbers, tables as text).
3. Chunk by structure (sections, then ~300–800 tokens with small overlap); store the title and heading path with each chunk so it makes sense alone.
4. Embed chunks in batches; store vector, text, document id, page, ACL groups, updated time.
5. Deleted or permission-changed documents are removed or re-tagged: stale chunks are a correctness and security bug.

**Query** (online):

1. Authenticate; look up the user's groups.
2. Optionally rewrite the question (resolve "it" from chat history) with a cheap model.
3. **Hybrid retrieval** filtered by the user's groups: vector search for meaning plus keyword search for exact terms, merged with reciprocal rank fusion; take the top ~30.
4. **Rerank** to the best ~5–8 chunks.
5. Build the prompt: system rules ("answer only from the sources; cite them; say you don't know otherwise"), the chunks in XML tags with ids, the question.
6. Stream the answer; map cited ids back to document links.
7. Log everything: question, retrieved ids, scores, tokens, latency, model, feedback.

### Step 4: scaling and reliability (7 min)

- **Back-of-envelope:** 2M chunks × 1,024-dim float32 vectors ≈ 2M × 4 KB ≈ 8 GB. One Postgres instance with an HNSW index handles that; a dedicated vector database is an option later, not a starting point.
- **20 QPS** is mostly bounded by LLM latency, not retrieval. Stateless query services scale horizontally behind a load balancer.
- **Caching:** cache embeddings of repeated questions; use prompt caching for the long, fixed system prompt; consider caching answers to very frequent questions (with care around permissions).
- **Rate limits and outages:** retries with backoff on 429/5xx, a fallback model, timeouts, and a graceful "try again" message.
- **Ingestion spikes:** a queue with workers, so a bulk upload doesn't slow down queries.

### Step 5: evals and monitoring (5 min)

This is where you can stand out:

- **Offline eval set:** 100–300 real questions with reference answers and expected source documents, built with subject-matter experts.
- **Retrieval metrics:** hit rate @k / recall @k (was the right chunk retrieved?).
- **Answer metrics:** correctness and faithfulness (is every claim supported by the cited chunks?), graded by an LLM judge that you've checked against human labels.
- **Run evals on every change** to prompts, chunking, models or retrieval: a regression gate in CI.
- **Online:** thumbs up/down, "I don't know" rate, escalations, latency p50/p95, cost per answer. Sample traces weekly and add failures to the eval set.

### Step 6: cost (3 min)

Estimate out loud, showing your assumptions:

```
Questions/day:        2,000 users × 5 = 10,000
Tokens per question:  ~4,000 input (system + 6 chunks + question), ~300 output
Mid-tier model (Sonnet 5.5, $2 / $10 per 1M tokens):
  input  10,000 × 4,000 = 40M tokens × $2/1M  = $80/day
  output 10,000 × 300   = 3M tokens  × $10/1M = $30/day
  ≈ $110/day ≈ $3,300/month
Levers: prompt caching on the fixed prefix, fewer/shorter chunks after reranking,
a cheaper model for simple questions (Haiku 5.5 is ~20× cheaper), caching frequent answers.
```

Then close with the trade-offs: "I'd start with Postgres and one model, measure, and only add complexity like a separate vector DB or routing between models once the evals or the bill say we need it."

> **Try it:** Do this design out loud, timed, for a different prompt: "Design a support-ticket triage assistant for an e-commerce company." Use the same six steps.

## 7. Common LLM interview questions, with good answers

**What is a token, and why does it matter?**
A chunk of text the model reads and writes, roughly ¾ of an English word. Pricing, context limits and latency are all measured in tokens, so token counts drive cost and design decisions such as how many chunks you retrieve.

**What's a context window?**
The maximum number of tokens the model can take in one request (input plus output). The API is stateless, so chat history, retrieved documents and instructions all compete for that space, and more context also means more cost and latency.

**RAG or fine-tuning?**
RAG when the model needs knowledge that changes or must be cited (company documents, prices): update the index, not the model. Fine-tuning when you need a consistent style, format or narrow behaviour that prompting can't reach, with plenty of examples. Most products start with prompting plus RAG, because it's cheaper, faster to iterate on and easier to evaluate.

**How do you reduce hallucinations?**
Ground answers in retrieved sources and ask for citations; instruct the model to say it doesn't know when the sources don't cover the question; improve retrieval (most "hallucinations" in RAG are retrieval misses); validate structured output against a schema; and measure faithfulness with evals rather than trusting spot checks.

**How do embeddings and vector search work?**
An embedding model maps text to a vector so that similar meanings are close together. You embed chunks once, embed the query at request time, and find the nearest chunks by cosine similarity, using an approximate index like HNSW at scale. Exact terms (codes, names) can be missed, which is why hybrid search adds keyword search.

**How do you evaluate an LLM feature?**
Build a representative eval set from real inputs, define metrics per component (retrieval recall, answer correctness, faithfulness, format validity), grade with code where possible and an LLM judge where needed (checked against human labels), and run the evals on every change. Online, track user feedback, latency and cost.

**How do you cut cost or latency?**
Use the smallest model that passes your evals; route easy requests to a cheaper model; trim context (fewer, better chunks); use prompt caching for repeated prefixes; stream responses so users see the first token fast; batch offline work; cache repeated results.

**What is prompt injection, and how do you defend against it?**
Untrusted text (a user message, a retrieved document, a web page) containing instructions the model might follow. Defences: keep instructions and data clearly separated (e.g. in tags) and tell the model data is not instructions; give tools the least privilege needed; require confirmation for risky actions; validate outputs; and never put secrets where the model could reveal them.

**Agents versus workflows?**
A workflow is a fixed sequence of LLM and code steps you design; an agent lets the model choose tools in a loop until done. Workflows are more predictable, cheaper and easier to test; use an agent only when the steps genuinely can't be known in advance, and then add step limits, tracing and evals.

**What about temperature?**
On older models it controlled randomness in sampling. On current Claude models the sampling parameters are fixed and sending them returns an error, so you get consistency through clear prompts, examples, structured output and evals instead.

## 8. Behavioural questions

Use the **STAR** shape: Situation, Task, Action, Result. Keep each answer to about two minutes and make the result concrete. Prepare stories for:

- **A hard bug** you tracked down (a retrieval miss, a cost blow-up).
- **A time you learned something fast** (going from rusty Python to shipped LLM products in three months is a great story).
- **A disagreement or difficult client** and how you handled it.
- **A failure** and what you changed afterwards.
- **Why AI engineering, and why this company** (specific to their product).

Your marketing background is a story too: you understand users and business value, which many engineering candidates don't.

## Common mistakes

- **Rushing into code** without clarifying the problem or edge cases.
- **Coding silently.** Interviewers grade your reasoning; narrate it.
- **Claiming numbers you can't explain.** Every number on your resume will be questioned.
- **Designing for Google scale on day one.** Start simple, estimate, then scale the bottleneck.
- **Forgetting evals, permissions and cost** in system design: the three things that most distinguish an AI engineer.
- **Generic applications.** A tailored first paragraph or a referral beats a hundred identical ones.
- **Not asking questions at the end.** Ask about their eval process, their stack and what a great first month looks like.

## Recap

- Find roles on startup boards, career pages, LinkedIn, X, local tech companies and through referrals; apply steadily.
- A one-page resume led by shipped projects, each bullet an action, a technical choice and a number.
- The loop: screen, practical Python, project deep-dive, LLM system design, behavioural.
- For coding rounds: clarify, example, simple solution, test, improve, all out loud.
- For RAG design: requirements (including permissions and freshness), components, data flow, scaling, evals and cost.
- Know clear answers to the common LLM questions; NeetCode 150 later only if you target big tech.
