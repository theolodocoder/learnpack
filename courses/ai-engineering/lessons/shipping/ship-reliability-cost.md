# Reliability, auth and cost control

## Why this matters

A public LLM endpoint is a machine that turns other people's requests into charges on your card. Without auth, anyone who finds the URL can use it. Without rate limits, one script can drain a month's budget overnight. And when Anthropic returns 529 "overloaded" during a busy hour, your app should degrade politely rather than return a wall of 500s. This lesson covers the controls that make an AI backend safe to leave running: who can call it, how often, how much each call costs, and what happens when things fail.

## 1. API keys, stored as hashes

For a backend used by programs or a handful of clients, **API keys** are the simplest auth that works. (User-facing apps with logins use sessions or OAuth, usually from a provider like Clerk, Auth0 or Supabase. Don't build password login yourself for a gig.)

In *FastAPI fundamentals* you compared the `X-API-Key` header against one key from settings. With several clients you need a key per client, so you can see who is calling and revoke one key without affecting the others. Store them like passwords: **never the key itself, only a hash.** If your database leaks, hashes are useless to the attacker.

```python
import hashlib
import hmac
import secrets


def generate_api_key(prefix: str = "sk_live") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"      # 32 random bytes -> 43 characters


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, stored_hash: str) -> bool:
    if not key or not stored_hash:
        return False
    return hmac.compare_digest(hash_api_key(key), stored_hash)
```

- **`secrets`, never `random`**, for anything security-related: `random` is predictable.
- **Show the key once,** when it's created, and store only `hash_api_key(key)`. If the client loses it, issue a new one.
- **SHA-256 is fine here** because the key is 256 bits of randomness: there's nothing to guess. Passwords people choose are short and guessable, so they need a deliberately slow hash (bcrypt, scrypt, argon2) instead.
- **`hmac.compare_digest`** takes the same time whether the first character or the last one differs. A plain `==` can return faster on an early mismatch, which in principle leaks information through timing.
- **The prefix** (`sk_live_`) makes keys recognisable in logs and lets secret scanners spot them if they leak.

Looking up a key in the database is a query on the hash:

```sql
CREATE TABLE api_keys (
    id          BIGSERIAL PRIMARY KEY,
    key_hash    TEXT NOT NULL UNIQUE,
    owner       TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at  TIMESTAMPTZ
);
```

```python
from typing import Annotated

from fastapi import Depends, Header, HTTPException


def require_client(x_api_key: Annotated[str | None, Header()] = None, db=Depends(get_db)) -> str:
    if not x_api_key:
        raise HTTPException(401, "Invalid or missing API key")
    row = db.execute("SELECT owner FROM api_keys WHERE key_hash = %s AND revoked_at IS NULL",
                     (hash_api_key(x_api_key),)).fetchone()
    if row is None:
        raise HTTPException(401, "Invalid or missing API key")
    return row[0]          # the owner: use it for rate limits, quotas and logs
```

Return the same message for "missing" and "wrong", so callers can't probe which keys exist. Revoking a key is one `UPDATE`.

## 2. Rate limiting with a token bucket

A rate limit caps how often each client can call you. The **token bucket** is the standard algorithm because it allows short bursts while enforcing an average rate:

- Each client has a bucket holding up to `capacity` tokens. It starts full.
- Tokens drip back in at `refill_per_sec`, up to `capacity`.
- Each request takes one token. No token, no request: **429 Too Many Requests**.

With `capacity=10, refill_per_sec=0.5`, a client can fire 10 requests at once, then sustain one every 2 seconds (30 a minute).

```python
import math
import time


class TokenBucket:
    def __init__(self, capacity: float, refill_per_sec: float, clock=time.monotonic):
        self.capacity, self.refill_per_sec, self.clock = capacity, refill_per_sec, clock
        self.tokens = float(capacity)
        self.updated = clock()

    def _refill(self) -> None:
        now = self.clock()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.refill_per_sec)
        self.updated = now

    def allow(self, cost: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def retry_after(self, cost: float = 1.0) -> float:
        self._refill()
        return max(0.0, (cost - self.tokens) / self.refill_per_sec)
```

No background timer is needed: the bucket works out how many tokens arrived since it last looked. `time.monotonic` is used because it never jumps backwards when the system clock is adjusted, and the injected `clock` means tests can move time by hand instead of sleeping.

As a FastAPI dependency, keyed by the client that `require_client` identified:

```python
buckets: dict[str, TokenBucket] = {}


def rate_limit(client_id: str = Depends(require_client)) -> str:
    bucket = buckets.setdefault(client_id, TokenBucket(capacity=10, refill_per_sec=0.5))
    if not bucket.allow():
        wait = max(1, math.ceil(bucket.retry_after()))
        raise HTTPException(429, "Too many requests", headers={"Retry-After": str(wait)})
    return client_id


@app.post("/ask")
async def ask(req: AskRequest, client_id: str = Depends(rate_limit)): ...
```

`Retry-After` tells well-behaved clients how long to wait. This is the same header you respect when *Anthropic* rate-limits *you*.

Things to know before relying on it:

- **The dict lives in one process.** With two instances (or uvicorn `--workers 2`), each has its own buckets and a client gets double the limit. When you scale out, keep buckets in **Redis** (a shared in-memory store; both Railway and Render offer it).
- **Rate limits by request count don't cap cost.** One request with a 100,000-token document costs as much as hundreds of small ones. Add a **token quota** per client per day: after each call, add `input_tokens + output_tokens` to the client's counter and refuse with 429 once it's over. Or charge the bucket a `cost` proportional to the request's size.
- **Unauthenticated routes** (a public demo) can be limited by client IP, but behind a platform proxy you must read the real IP from `X-Forwarded-For` as configured for your platform.

## 3. Caching repeated answers

Support bots and FAQ assistants get the same questions constantly. If the inputs are identical, so is a good answer: serve it from a cache, instantly and for free.

The cache **key** must include everything that changes the answer (model, system prompt, messages, and any parameters such as `max_tokens` or tools), and must not depend on dict ordering. Hash a canonical JSON encoding:

```python
import hashlib
import json


def cache_key(model: str, system: str, messages: list[dict]) -> str:
    payload = json.dumps({"model": model, "system": system, "messages": messages},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()
```

Entries need a **TTL** (time to live): documents get updated, prompts get improved, and a stale answer should eventually go away.

```python
class TTLCache:
    def __init__(self, ttl_seconds: float, clock=time.monotonic):
        self.ttl, self.clock = ttl_seconds, clock
        self._data: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> str | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if self.clock() >= expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: str) -> None:
        self._data[key] = (self.clock() + self.ttl, value)
```

Then check the cache before calling Claude and store successful answers after. Never cache errors.

When **not** to cache: personalised answers (the key must include the user, or don't cache), conversations (long histories rarely repeat exactly), and anything time-sensitive. In production use Redis with `SET key value EX 3600`, which gives TTLs and sharing between instances. For a RAG app, include the retrieved chunk ids in the key, or clear the cache when documents change.

## 4. Prompt caching on the Claude API

Response caching only helps when the *whole* request repeats. **Prompt caching** helps when the *start* of the request repeats, which in LLM apps is nearly always: the same long system prompt, the same tool definitions, the same document, with a different question at the end.

How it works: you mark a point in the prompt with `cache_control`. The first request **writes** everything up to that point (the *prefix*) to Anthropic's cache. Later requests with an **identical prefix** **read** it instead of processing it again, which is faster and much cheaper.

```python
handbook = open("handbook.md").read()          # say ~20,000 tokens, the same every call

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    system=[
        {"type": "text", "text": "Answer questions using only the handbook below. Cite section numbers."},
        {"type": "text", "text": handbook, "cache_control": {"type": "ephemeral"}},   # cache up to here
    ],
    messages=[{"role": "user", "content": question}],                                 # changes every call
)

u = response.usage
print(u.cache_creation_input_tokens, u.cache_read_input_tokens, u.input_tokens)
# first call:  20012     0  15     (wrote the prefix to the cache)
# second call:     0 20012  17     (read it from the cache)
```

The rules, from Anthropic's prompt caching docs:

- **Order is `tools`, then `system`, then `messages`.** The cached prefix is everything up to and including the block with `cache_control`. Put stable content first and anything that varies after the breakpoint.
- **The prefix must match exactly.** A timestamp, a user's name or a shuffled tool list early in the system prompt changes the prefix on every call, and nothing is ever read from the cache. This is the most common reason caching "doesn't work".
- **Minimum length:** prompts shorter than the model's minimum aren't cached (no error, just no caching). For Opus 5.5, Sonnet 5.5 and Haiku 5.5 the minimum is 512 tokens; older models need more.
- **Lifetime:** 5 minutes by default, refreshed for free every time the entry is read. For traffic that's more spread out, `{"type": "ephemeral", "ttl": "1h"}` keeps it an hour.
- **Up to 4 breakpoints** per request, e.g. one after the tools, one after the system prompt, one near the end of a long conversation. The API also accepts a single top-level `cache_control` field (*automatic caching*) that places the breakpoint on the last cacheable block for you and moves it forward as a conversation grows.

**Reading usage.** With caching, the request's input is split three ways, and total input = `cache_read_input_tokens + cache_creation_input_tokens + input_tokens`:

- `cache_creation_input_tokens`: written to the cache on this request. Billed at **1.25×** the base input price (2× for the 1-hour TTL).
- `cache_read_input_tokens`: read from the cache. Billed at a small fraction of the input price: **0.05×** on Opus 5.5 and Sonnet 5.5, 0.1× on most other models.
- `input_tokens`: the uncached tokens after the last breakpoint, at the normal price.

**The arithmetic,** for a 20,000-token handbook on Opus 5.5 ($4 per million input tokens):

```
without caching:   20,000 × $4.00/M  = $0.080   every call
cache write:       20,000 × $5.00/M  = $0.100   once per 5 minutes (1.25×)
cache read:        20,000 × $0.20/M  = $0.004   every other call (0.05×)
```

At one question a minute, the input cost drops by about 90%, and responses start faster because the cached part isn't processed again. Log `cache_read_input_tokens` in your traces and watch the hit rate: if it's zero, something in your prefix is changing.

> **Note:** Prompt caching and response caching stack. The response cache answers exact repeats for free; prompt caching makes every other call over the same document cheap.

## 5. Timeouts and retries

From *Serving Claude from FastAPI*: set a client timeout (`AsyncAnthropic(timeout=60.0)`), and remember the SDK already retries 429, 5xx and 529 errors twice with exponential backoff (`max_retries=2`). For other services (an embedding API, a web search tool) you write the loop yourself:

```python
import random
import time

RETRYABLE = {408, 409, 429, 500, 502, 503, 504, 529}


def with_retries(fn, *, attempts: int = 4, base: float = 0.5, cap: float = 8.0, sleep=time.sleep):
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status not in RETRYABLE or attempt == attempts - 1:
                raise
            sleep(random.uniform(0, min(cap, base * 2 ** attempt)))   # exponential backoff, full jitter
```

- **Retry only what can succeed next time:** rate limits, overloads, server errors, timeouts. A 400 or 401 will fail identically forever.
- **Backoff with jitter.** Doubling the wait gives the service room to recover; the random part stops a thousand clients from retrying at the same instant.
- **Bound the total time.** In a web request, a person is waiting: two quick retries, then give up and degrade. Batch jobs can retry for longer.
- **Don't stack retry layers.** If the SDK retries twice and your loop retries four times around it, one failure becomes twelve calls.
- **Only retry safe operations.** Retrying a "send email" tool call may send it twice.

## 6. Graceful degradation and fallbacks

When retries run out, choose a worse-but-useful answer over an error. Options, from cheapest:

1. **A stale cached answer.** If the cache has an expired entry for this question, it's probably still fine.
2. **A fallback model.** If Opus is overloaded, Sonnet or Haiku can usually answer. Only fall back on *availability* errors, not on 400s:

   ```python
   def create_with_fallback(client, models: list[str], **kwargs):
       last_error = None
       for model in models:
           try:
               return client.messages.create(model=model, **kwargs)
           except Exception as e:
               if getattr(e, "status_code", None) not in (429, 500, 529):
                   raise                      # our bug or a bad request: don't hide it
               last_error = e
       raise last_error

   response = create_with_fallback(client, ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"],
                                   max_tokens=1024, messages=messages)
   ```

   Log which model actually answered, and run your evals against the fallback too, so you know its quality is acceptable.
3. **A partial answer.** A RAG app can return the top retrieved passages with "The AI summary is unavailable right now", which is still useful.
4. **A clear, honest error:** 503 with `Retry-After` and a message a person understands, never a stack trace.

If an upstream keeps failing, stop hammering it. A **circuit breaker** counts recent failures and, past a threshold, skips the call entirely for a short cool-down, going straight to the fallback. That protects your latency and stops you adding load to a struggling service.

## Common mistakes

- **Storing API keys in plain text,** or generating them with `random`.
- **Comparing keys with `==`** instead of `hmac.compare_digest`.
- **In-memory rate limits with several instances,** silently multiplying the limit.
- **Limiting requests but not tokens,** so one huge request costs as much as a thousand small ones.
- **A cache key missing an input** (model, system prompt, user), so one user gets another's answer.
- **Something variable before the prompt-cache breakpoint** (a date, a request id), so the cache never hits. Check `cache_read_input_tokens`.
- **Retrying 400s,** retrying without jitter, or stacking retries on top of the SDK's.
- **Silent fallbacks,** so you never notice production has been running on the cheaper model for a week.

## Recap

- Issue one random key per client (`secrets.token_urlsafe`), store its SHA-256 hash, verify with `hmac.compare_digest`, and revoke by row.
- A token bucket allows bursts up to `capacity` and an average of `refill_per_sec`; return 429 with `Retry-After`. Move buckets to Redis when you run several instances, and add per-client token quotas.
- Cache identical requests by a SHA-256 of a canonical JSON of model, system and messages, with a TTL; never cache errors or personalised answers under a shared key.
- Prompt caching: stable content first (tools, system, documents), `cache_control: {"type": "ephemeral"}` at the end of it, at least 512 tokens on current models, 5-minute TTL by default. Reads cost 0.05× input on Opus 5.5; confirm with `usage.cache_read_input_tokens`.
- Retry only retryable errors with exponential backoff and jitter, within a time budget.
- Degrade gracefully: stale cache, fallback model, partial answer, then a clear 503, and log which path was used.
