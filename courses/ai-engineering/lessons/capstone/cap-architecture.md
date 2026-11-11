# From spec to architecture

## Why this matters

A spec says *what* and *for whom*. An architecture says *how*: which pieces exist, what data they hold, where the model is called, what happens when something fails, and what it costs. Clients and interviewers both ask the same question: "Walk me through how it works." A clear architecture written down in week 9 is what lets you answer that, and it stops you from building an agent when one prompt would do.

## 1. Pick the simplest pattern that works

You've met four patterns. They form a ladder: each step adds power, cost, latency and ways to fail. Start at the bottom and climb only when you have evidence you need to.

| Pattern | What it is | Use when | Example |
|---|---|---|---|
| **Single call** | One prompt in, one answer out (often structured output) | The input contains everything the model needs | Meeting transcript → summary + action items |
| **Workflow** | A fixed sequence of calls and code steps that *you* control | The task has clear stages, each checkable | Job post → extract requirements → match CV → rewrite → check for invented facts |
| **RAG** | Retrieve relevant documents, then one call that answers from them | The knowledge is too big for the prompt, or changes often | Shop bot answering from a price list of 2,000 items and a long FAQ |
| **Agent** | The model decides which tools to call, in a loop, until done | The steps can't be known in advance | "Find three jobs that fit my CV, check each company's careers page, draft applications" |

Two practical notes:

- **Small knowledge fits in the prompt.** A shop with 60 products and a one-page FAQ is maybe 4,000 tokens. Put it in the system prompt and skip retrieval entirely. Add RAG when it stops fitting, or when cost per message gets too high. Prompt caching makes a large, unchanging system prompt much cheaper on repeated calls.
- **An agent is a last resort for a capstone.** It's harder to evaluate, slower, costlier and less predictable. If you can write the steps down, it's a workflow. Anthropic's article *Building effective agents* makes the same argument.

For the three worked examples from *Choosing a problem worth three weeks*: meeting notes is a **single call**, the job assistant is a **workflow**, and the shop bot is a **single call with the data in the prompt**, becoming **RAG** if the catalogue is big.

## 2. Draw the boxes

Every capstone has the same handful of components. Name yours:

```
 ┌──────────┐     ┌───────────────────────────── FastAPI backend ─────────────────────────────┐
 │ Channel  │────▶│ routes ─▶ validation ─▶ core logic ─▶ LLM client ─▶ Claude API            │
 │ (web UI, │◀────│                │             │                                            │
 │ WhatsApp)│     │                ▼             ▼                                            │
 └──────────┘     │          rate limiter    store (SQLite/Postgres): users, conversations,  │
                  │                          messages, documents, feedback                    │
                  └───────────────────────────────────────────────────────────────────────────┘
                              │ logs + traces + cost per call ─▶ your tracing tool
```

The **channel** is how users reach you (a web frontend, a WhatsApp number, email). The **backend** holds the keys, the prompts and the logic. The **store** keeps state, because the Claude API is stateless: you must store and resend the conversation history yourself. **Observability** (logs, traces, token counts) is how you'll know what users actually did.

## 3. The data model

Write down your tables before you write code. Most capstones need only four or five. Here's the shop bot in SQLite, which is plenty for three users and easy to move to Postgres later:

```python
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    channel_id  TEXT NOT NULL UNIQUE,      -- WhatsApp user id, email, or web session
    consented   INTEGER NOT NULL DEFAULT 0, -- agreed to conversation logging
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS messages (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    external_id   TEXT UNIQUE,              -- the channel's message id: makes retries idempotent
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content       TEXT NOT NULL,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS feedback (
    message_id  INTEGER PRIMARY KEY REFERENCES messages(id),
    rating      TEXT CHECK (rating IN ('up', 'down')),
    correction  TEXT
);
"""

db = sqlite3.connect(":memory:")
db.executescript(SCHEMA)
db.execute("INSERT INTO users (channel_id) VALUES (?)", ("2348031234567",))
print(db.execute("SELECT id, channel_id, consented FROM users").fetchall())
# [(1, '2348031234567', 0)]
```

Three decisions are baked in there, and each one comes from a later lesson:

- `external_id UNIQUE` on messages: webhooks retry, and a unique constraint is the simplest way to make sure the same message is processed once (*Messaging channels*).
- `consented` on users: you only log conversations for people who agreed (*User testing and iteration*).
- Token counts per message: that's your cost tracking, for free.

## 4. API design

Keep the API small and boring. List every route with its method, body and response before writing any:

```
GET  /health                     -> {"status": "ok"}                       (no auth; for the host)
POST /chat                       {"message": str, "conversation_id": int?} -> {"reply": str, "conversation_id": int}
POST /chat/stream                same body                                 -> text/event-stream
POST /feedback                   {"message_id": int, "rating": "up"|"down", "correction": str?} -> 204
GET  /webhook  (WhatsApp)        verification handshake                    -> challenge as text
POST /webhook  (WhatsApp)        Meta's payload, signed                    -> 200 always, quickly
```

Rules of thumb that carry over from the backend lessons:

- The **backend** chooses the model, system prompt and `max_tokens`. The client sends only the user's message and ids.
- Validate everything with Pydantic and put limits on lengths. A 50,000-character "message" is a cost attack.
- Return `conversation_id` so the frontend can continue a conversation; the backend loads the history from the store.

## 5. Where the LLM sits

Be explicit about every place you call Claude: the purpose, the model, the input, and the output shape. For the job assistant:

| Step | Model | Input | Output |
|---|---|---|---|
| Extract requirements | `claude-haiku-5-5` | job post text | `Requirements` Pydantic model (skills, years, must-haves) |
| Rewrite CV | `claude-opus-5-5` | CV + requirements | tailored CV in Markdown |
| Check for invention | `claude-haiku-5-5` | original CV + tailored CV | `{"invented": [str]}`; if non-empty, retry or flag |

Notice the pattern: **cheap model for narrow structured steps, strong model for the step users judge.** Prices per million tokens (input / output) are Opus 5.5 $4 / $20, Sonnet 5.5 $2 / $10, Haiku 5.5 $0.10 / $0.50, so the choice matters a lot at volume.

Everything that isn't language goes in plain code: dates, sums, lookups, sending messages. A model shouldn't compute a delivery fee; your code should look it up and hand the result to the model.

## 6. Failure modes

List what can go wrong and decide now what the user sees. This table is worth putting in your README:

| Failure | Likely cause | What the user sees | What you do |
|---|---|---|---|
| Claude 429 / 529 / 5xx | rate limit, overload | "Busy, please try again" or, in chat, a fallback message | SDK retries twice; then fall back; alert if frequent |
| Claude 400 | bug in your request | Fallback message | Log and fix; don't retry |
| Timeout | slow response | Fallback after N seconds | Client `timeout=`; stream where possible |
| Wrong or invented answer | missing data, weak prompt | A confident wrong answer (the worst case) | Grounding, "I don't know" path, human hand-off, evals |
| Duplicate webhook | the channel retries | Two replies | Idempotency on message id |
| Abuse / cost spike | public link shared | Nothing, until your bill | Per-user rate limits, input length caps, spend alerts |
| Store down | database restart | Error page | Health check; host restarts the app |

The fourth row is the one that loses users. Decide your "I don't know" behaviour now: for the shop bot, "I'm not sure, I've asked Kemi to reply" plus a notification to the owner.

## 7. Cost per user per month

Estimate before you build, and again after real usage. The formula:

```
messages per month = users · messages per user
cost = messages · (input tokens · input price + output tokens · output price) / 1,000,000
```

Input tokens per message include the system prompt, the conversation history you resend and any retrieved context. That's usually far bigger than the user's message.

```python
def monthly_cost(users, msgs_per_user, in_tokens, out_tokens, in_price, out_price):
    messages = users * msgs_per_user
    return messages * (in_tokens * in_price + out_tokens * out_price) / 1_000_000

# Shop bot: 1 shop, ~1,500 customer messages a month, 3,000 tokens in (prompt + price list + history), 150 out.
print(round(monthly_cost(1, 1500, 3000, 150, 4.00, 20.00), 2))   # Opus 5.5:  22.5
print(round(monthly_cost(1, 1500, 3000, 150, 0.10, 0.50), 2))    # Haiku 5.5: 0.56
```

$22.50 a month for one shop on the strongest model, or under a dollar on Haiku. Now you can reason like a business: if the shop would pay ₦10,000 a month, which model leaves you a margin? Is Haiku good enough on your eval set? (That's a question your evals answer, not your intuition.) Remember the channel can cost money too: WhatsApp charges per delivered message in most categories, so check Meta's current pricing for your market.

> **Try it:** Do the cost estimator exercise, then put your own product's numbers in. Write the result into your spec.

## 8. A sequence diagram

A sequence diagram shows one request flowing through the system in time order. There's no diagram renderer here, so write it as text. Mermaid syntax renders automatically on GitHub, which makes it perfect for your README:

```
sequenceDiagram
    participant U as Customer (WhatsApp)
    participant M as Meta Cloud API
    participant B as FastAPI backend
    participant D as SQLite
    participant C as Claude
    U->>M: "Do you deliver to Ibadan?"
    M->>B: POST /webhook (signed)
    B->>B: verify signature
    B->>D: insert message (external_id unique)
    B-->>M: 200 OK
    B->>D: load history + shop info
    B->>C: messages.create(system, history)
    C-->>B: reply + usage
    B->>D: save reply + token counts
    B->>M: POST /{phone-number-id}/messages
    M->>U: "Yes, 2 days, ₦3,500"
```

Notice two things the diagram makes obvious. The backend answers Meta with `200` *before* calling Claude, so a slow model never causes a webhook retry. And every arrow is a place that can fail: check each against your failure table.

## 9. Write an ADR

An **architecture decision record** is a short note recording one significant decision: the context, the decision, and its consequences. Future you (and a client, or an interviewer reading your repo) will want to know *why* you chose SQLite, or why there's no agent. Keep them in `docs/adr/`, numbered, one decision per file, never edited after the fact (if you change your mind, write a new ADR that supersedes the old one).

```markdown
# ADR 001: Put the shop's catalogue in the prompt instead of using RAG

Status: Accepted (2026-11-16)

## Context
Kemi's Fashion has 64 products and a one-page FAQ, about 4,500 tokens in total.
The catalogue changes weekly. We need correct prices; wrong prices lose trust.

## Decision
Load the full catalogue and FAQ into the system prompt on every call, from a CSV the owner
updates. No embeddings or vector store for now.

## Consequences
- Simpler: no ingestion pipeline, no retrieval errors; the model always sees every price.
- Cost: ~4,500 extra input tokens per message (~$0.0005 on Haiku 5.5); prompt caching reduces it.
- Revisit if the catalogue passes ~300 products or input cost per message passes $0.002.
```

Three to five ADRs is right for a capstone: pattern choice, model choice, storage, channel, and maybe hosting.

## Common mistakes

- **Starting with an agent.** If you can list the steps, write a workflow.
- **Adding RAG for data that fits in the prompt.** Retrieval is a new way to be wrong. Earn it.
- **Letting the model do arithmetic or lookups.** Code computes; the model explains.
- **Forgetting history is your job.** The API is stateless. Store messages and resend what's needed.
- **No cost estimate.** Then the first time you learn your cost is from the bill.
- **Calling Claude before acknowledging a webhook.** Slow replies cause retries, which cause duplicate answers.
- **Architecture only in your head.** Write the diagram, the failure table and the ADRs into the repo. They're a large part of what makes the project look professional.

## Recap

- Climb the ladder only as far as you need: single call → workflow → RAG → agent.
- Name the components: channel, backend, store, LLM client, observability.
- Design the tables and routes first; bake in idempotency, consent and token counts.
- Document every LLM call: purpose, model, input, output shape. Code does what isn't language.
- List failure modes and what the user sees for each; plan an "I don't know" path.
- Estimate cost per user per month with the formula, and record decisions in short ADRs.
