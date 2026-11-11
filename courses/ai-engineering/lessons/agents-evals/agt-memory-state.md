# Memory and state

## Why this matters

An agent that helps a customer for twenty turns, or works through a 40-step task, runs into two walls. Its message history grows until it costs a fortune per call and eventually doesn't fit in the context window. And when the process restarts (a deploy, a crash, a user who comes back tomorrow) everything in that history is gone. Memory is how you get past both: keep the working context small and relevant, save what matters somewhere durable, and be able to pick a task up where it stopped.

## 1. History grows, and you pay for all of it

The API is stateless, so every call sends the **whole** conversation. In an agent loop that includes every tool result. Suppose each turn adds about 1,500 tokens (a tool call, a result, a bit of text):

```python
per_turn = 1_500
total_input = sum(per_turn * t for t in range(1, 21))   # 20 turns, each resends everything before it
print(total_input)                     # 315000 input tokens
print(total_input * 4 / 1_000_000)     # 1.26  -> dollars on Opus 5.5 ($4 per million input tokens)
```

Input cost grows with the **square** of the number of turns: turn 20 alone sends 30,000 tokens. Long tool outputs (a whole web page, a 500-row query result) make it far worse. Two habits help before you need anything clever:

- **Keep tool outputs small.** Return the 5 most relevant rows, not 500; a page's main text, not its HTML. Tool design is memory design.
- **Measure.** `client.messages.count_tokens(model=..., messages=messages).input_tokens` tells you what the next call will cost before you make it, and `response.usage.input_tokens` tells you after.

> **Note:** Prompt caching can make repeated prefixes much cheaper, but it doesn't make the context window bigger. You still need to manage what's in it.

## 2. The context budget

Decide a **budget** for the history (say 50,000 tokens) and act when you cross it. There are three tools, from crude to clever:

1. **Trim:** drop the oldest turns. You did this in *How LLMs work* with `trim_history`. It's cheap but forgets: the user's name from turn 1 disappears.
2. **Clear old tool results:** replace the content of old `tool_result` blocks with a placeholder like `"[old result removed]"`. The model keeps the record that it called the tool, which is usually enough, and tool results are typically the largest part of an agent's history.
3. **Summarise:** replace old turns with a short summary written by a cheap model, and keep the newest turns word for word.

Here's clearing old tool results, keeping the latest few untouched:

```python
def clear_old_tool_results(messages: list[dict], keep_last: int = 3) -> list[dict]:
    """Blank out all but the newest `keep_last` tool results. Returns a new list."""
    positions = [(i, j) for i, m in enumerate(messages) if isinstance(m["content"], list)
                 for j, block in enumerate(m["content"])
                 if isinstance(block, dict) and block.get("type") == "tool_result"]
    to_clear = set(positions[:-keep_last]) if keep_last else set(positions)
    out = []
    for i, m in enumerate(messages):
        if isinstance(m["content"], list):
            m = {**m, "content": [{**b, "content": "[old tool result cleared]"} if (i, j) in to_clear else b
                                  for j, b in enumerate(m["content"])]}
        out.append(m)
    return out
```

Note it keeps every `tool_result` block and its `tool_use_id`. Removing the block itself would break the pairing rule (every `tool_use` needs a matching result), and the API would reject the request.

### Summarising old turns

```python
def compact_history(client, messages, keep_last=6, model="claude-haiku-5-5"):
    split = len(messages) - keep_last
    while split > 0 and messages[split]["role"] == "assistant":
        split -= 1                                  # recent part must start with a user message
    if split <= 0:
        return list(messages)
    old, recent = messages[:split], [dict(m) for m in messages[split:]]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in old)
    summary = client.messages.create(
        model=model, max_tokens=1000,
        system="Summarise this conversation. Keep every name, number, decision, preference and open question.",
        messages=[{"role": "user", "content": f"<transcript>\n{transcript}\n</transcript>"}],
    ).content[0].text
    recent[0]["content"] = f"<summary>\n{summary}\n</summary>\n\n{recent[0]['content']}"
    return recent
```

Some details that matter:

- **Use a cheap model.** Summarising is easy; Haiku 5.5 does it for a fraction of a cent.
- **Tell it what to keep.** "Keep names, numbers, decisions and open questions" beats "summarise".
- **Keep the newest turns verbatim.** The model needs the exact recent wording to continue naturally.
- **Fold the summary into the first kept user message** (in tags), so roles still alternate and the first message is from the user.
- **Split at a safe point.** In an agent history, never split between an assistant `tool_use` and the user message carrying its `tool_result`; both sides must stay together.

> **Note:** The Claude API also offers server-side context management (automatic clearing of old tool results, and compaction). They're worth knowing about, but understand the hand-written version first so you know what they do and what they lose.

## 3. Short-term versus long-term memory

| | Short-term memory | Long-term memory |
|---|---|---|
| What | The message history of this session | Facts saved deliberately for later |
| Lives in | The `messages` list | A database |
| Lifetime | One conversation or task | Across sessions, restarts, weeks |
| How the model sees it | All of it, every call | Only what you retrieve and put in the prompt |

Long-term memory is RAG pointed at the agent's own notes. You already know the retrieval part from *RAG from scratch*: embed, store, search by cosine similarity. The new questions are **what** to save and **when** to recall.

### Saving facts

The simplest reliable design is to give the agent a tool:

```python
REMEMBER_TOOL = {
    "name": "remember",
    "description": (
        "Save a durable fact about the user for future conversations: preferences, account details, "
        "decisions. One short self-contained sentence. Don't save small talk or one-off details."
    ),
    "input_schema": {"type": "object", "properties": {"fact": {"type": "string"}},
                     "required": ["fact"], "additionalProperties": False},
}
```

The model decides what's worth saving (guided by the description), and you store it scoped to the user:

```python
import sqlite3

import numpy as np


class MemoryStore:
    def __init__(self, embed, path="memory.db"):
        self.embed = embed
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS memories("
                        "id INTEGER PRIMARY KEY, user_id TEXT, fact TEXT, vector BLOB)")

    def remember(self, user_id: str, fact: str) -> int:
        vec = np.asarray(self.embed([fact])[0], dtype=np.float32)
        cur = self.db.execute("INSERT INTO memories(user_id, fact, vector) VALUES (?, ?, ?)",
                              (user_id, fact, vec.tobytes()))
        self.db.commit()
        return cur.lastrowid

    def recall(self, user_id: str, query: str, k: int = 3, min_score: float = 0.3) -> list[str]:
        q = np.asarray(self.embed([query])[0], dtype=np.float32)
        rows = self.db.execute("SELECT fact, vector FROM memories WHERE user_id = ?", (user_id,)).fetchall()
        scored = sorted(((float(np.frombuffer(v, dtype=np.float32) @ q), f) for f, v in rows), reverse=True)
        return [f for s, f in scored[:k] if s >= min_score]
```

SQLite stores the vector as raw bytes; NumPy turns it back. For thousands of users and millions of facts you'd move this to Postgres with pgvector exactly as in *SQL and Postgres*, with `user_id` as a filtered column.

### Recalling facts

At the start of each conversation (or each turn), retrieve memories relevant to the user's message and put them in the system prompt:

```python
facts = memory.recall(user_id, user_message)
system = BASE_SYSTEM
if facts:
    system += "\n\n<memories>\n" + "\n".join(f"- {f}" for f in facts) + "\n</memories>"
```

Alternatively, give the agent a `recall` tool and let it search when it decides it needs to. Automatic recall is simpler and more predictable; a tool scales better when there are many memories. Start with automatic.

**Rules for long-term memory:**

- **Scope by user, always.** Every query filters on `user_id`. One user's memories leaking into another's prompt is a privacy incident.
- **Let users see and delete what you saved.** A `forget` function and a "what do you remember about me?" path aren't optional in most jurisdictions.
- **Memories can be wrong or stale.** Store a timestamp; prefer newer facts; let new facts replace old ones ("Ada moved to Abuja" should win over "Ada lives in Lagos").
- **Memories can be poisoned.** If the agent saves facts from documents or web pages it read, an attacker can plant instructions that come back in every future session. Save facts from the user's own words, and treat recalled memories as data (more in *Prompt injection and agent security*).

## 4. Agent state and resuming a task

A long task (process 200 invoices, research 30 companies) will be interrupted. If its only state is a Python variable, you start over. Make the state an explicit object you can save after every step:

```python
import json
from pathlib import Path

from pydantic import BaseModel


class TaskState(BaseModel):
    task_id: str
    goal: str
    messages: list[dict] = []
    done_items: list[str] = []
    pending_items: list[str] = []
    status: str = "running"          # running | waiting_for_approval | done | failed
    spent_usd: float = 0.0


def save(state: TaskState, folder: Path = Path("runs")) -> None:
    folder.mkdir(exist_ok=True)
    (folder / f"{state.task_id}.json").write_text(state.model_dump_json(indent=2))


def load(task_id: str, folder: Path = Path("runs")) -> TaskState:
    return TaskState.model_validate_json((folder / f"{task_id}.json").read_text())
```

The worker loop becomes: load state, do one step, update state, save, repeat:

```python
def run(task_id: str):
    state = load(task_id)
    while state.pending_items and state.status == "running":
        item = state.pending_items[0]
        process(item)                                 # make this idempotent: safe to run twice
        state.pending_items.pop(0)
        state.done_items.append(item)
        save(state)
    state.status = "done"
    save(state)
```

Two things make resuming safe:

- **Save after every step**, so a crash loses at most one step.
- **Make steps idempotent**: running one twice has the same effect as once. If the crash happens after `process(item)` but before `save`, the item runs again on resume. Use upserts instead of inserts, and check "already sent?" before sending.

Messages from the SDK are objects, not dicts. To store `response.content` as JSON, convert it: `[block.model_dump() for block in response.content]`. The API accepts those dicts back on the next call.

State objects also make the **waiting** case clean: when an agent needs human approval, set `status = "waiting_for_approval"`, save, and stop. When the human answers (minutes or days later), load the state and continue. That's the subject of the next lesson.

> **Try it:** In the practice editor, build `MemoryStore` and check that a second store opened on the same file sees the facts the first one saved: that's long-term memory surviving a restart.

## Common mistakes

- **Letting history grow unbounded** until calls cost dollars each or fail with a context-length error.
- **Dropping a `tool_result` while keeping its `tool_use`** (or splitting the pair when summarising). The API rejects it.
- **Summaries that lose the facts** because the prompt didn't say what to keep.
- **Memory queries without a `user_id` filter.**
- **Saving everything** the agent reads as "memory", including injected text from web pages.
- **Agent state that only lives in RAM**, so a deploy restarts every running task from zero.
- **Non-idempotent steps**, so resuming sends the same email twice.

## Recap

- Each call resends the whole history; input cost grows roughly with the square of the number of turns.
- Keep tool outputs small, set a context budget, and trim, clear old tool results, or summarise old turns with a cheap model.
- Short-term memory is the message list; long-term memory is a per-user fact store recalled with embeddings.
- Scope, expose and expire memories; don't let untrusted content write to them.
- Keep task state in an explicit object, save it after every step, and make steps idempotent so tasks can resume.
