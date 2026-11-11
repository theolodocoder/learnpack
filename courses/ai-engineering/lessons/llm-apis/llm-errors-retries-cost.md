# Errors, retries and cost control

## Why this matters

A demo calls the API once and works. A product calls it thousands of times a day, and some of those calls **will** fail: you'll hit rate limits during a traffic spike, the API will occasionally be overloaded, networks drop. Meanwhile, a bug in a loop can quietly spend a month's budget in an afternoon. The difference between a toy and something a client trusts is how you handle failure and money: retry what's safe to retry, fail fast on what isn't, set timeouts, and know what every request costs.

## 1. What can go wrong

The SDK raises an exception for every failed request. The classes form a hierarchy, so you can catch broadly or precisely:

```
anthropic.APIError
├── anthropic.APIConnectionError        couldn't reach the API (network, DNS)
│   └── anthropic.APITimeoutError       request took longer than the timeout
└── anthropic.APIStatusError            the API answered with an error status (.status_code)
    ├── BadRequestError         400     your request is invalid
    ├── AuthenticationError     401     missing or bad API key
    ├── PermissionDeniedError   403     key not allowed to do this
    ├── NotFoundError           404     e.g. a model name that doesn't exist
    ├── RateLimitError          429     too many requests or tokens per minute
    └── InternalServerError     5xx     a problem on the API side (529 = overloaded)
```

Every `APIStatusError` has `.status_code` and `.response` (the raw HTTP response, including headers). Here's what each status tells you:

| Status | Meaning | Retry? |
|---|---|---|
| 400 | Invalid request: bad parameter, malformed messages, unsupported option. | **No.** The same request will fail again. Fix the code. |
| 401 / 403 | Key missing, invalid or not permitted. | **No.** |
| 404 | Unknown model or endpoint. | **No.** |
| 413 | Request too large. | **No.** Send less. |
| 429 | Rate limited. | **Yes**, after waiting. |
| 500 | Internal API error. | **Yes.** |
| 529 | API overloaded. | **Yes**, after waiting. |
| Connection error / timeout | Network trouble. | **Yes.** |

The rule: **4xx means you sent something wrong** (except 429, which means "too fast"); **5xx means the server had a problem**. Retrying a 400 just wastes time and hides the bug.

```python
import anthropic

client = anthropic.Anthropic()

try:
    response = client.messages.create(
        model="claude-opus-5-5", max_tokens=1000,
        messages=[{"role": "user", "content": "Hello"}],
    )
except anthropic.RateLimitError as e:
    print("Slow down:", e.response.headers.get("retry-after"), "seconds suggested")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
except anthropic.APIConnectionError:
    print("Could not reach the API")
```

Order matters: catch specific classes before their parents.

## 2. The SDK already retries

Before writing retry code, know that the SDK **retries twice by default** on connection errors, timeouts, 408, 409, 429 and 5xx, with a short exponential backoff. For many apps, that's enough. You can tune it:

```python
client = anthropic.Anthropic(max_retries=5)            # for every request
response = client.with_options(max_retries=0).messages.create(...)  # just this one
```

So why learn to write retries yourself?

- **Batch jobs** need longer, more patient retries than an interactive request (where the user won't wait a minute).
- You may want to **log** each failure, count them, or switch to a fallback model after repeated overloads.
- You'll call other APIs (weather, payments, your own services) that don't retry for you.
- It's a standard interview question, and the pattern applies everywhere.

## 3. Exponential backoff with jitter

When a request fails with a retryable error, don't retry instantly: the server is busy or you're over your limit, and hammering it makes things worse. Wait, and wait **longer each time**:

```
attempt 0 fails → wait ~1 s
attempt 1 fails → wait ~2 s
attempt 2 fails → wait ~4 s
attempt 3 fails → give up and raise
```

That's **exponential backoff**: `delay = base · 2ⁿ`.

Add **jitter**, a random extra amount. Without it, if 100 clients all got rate-limited at the same moment, they'd all retry at exactly the same moment too, and fail together again. Randomness spreads them out.

```python
import random
import time


def is_retryable(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    return status is not None and (status == 429 or status >= 500)


def call_with_retry(client, request: dict, max_retries: int = 3,
                    base_delay: float = 1.0, sleep=time.sleep):
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**request)
        except Exception as e:
            if not is_retryable(e) or attempt == max_retries:
                raise
            delay = base_delay * 2**attempt
            sleep(delay + random.uniform(0, delay))
```

Details worth noticing:

- **`getattr(error, "status_code", None)`** works with any exception: SDK errors, `httpx` errors you've wrapped, or the fake errors used in tests. An exception with no status (a bug in your own code, say a `KeyError`) isn't retried.
- **`raise` with no argument** re-raises the original exception with its traceback intact.
- **The `sleep` parameter.** Injecting the sleep function means tests can pass `delays.append` and check the delays without actually waiting. This "pass in your dependencies" style is the same reason all the exercises take `client` as a parameter.
- **A cap on attempts.** Never retry forever.

In real code you'd also retry `anthropic.APIConnectionError` (it has no status code but is worth retrying), and respect the `retry-after` header on a 429 when it's present:

```python
def retry_after_seconds(error) -> float | None:
    response = getattr(error, "response", None)
    value = response.headers.get("retry-after") if response is not None else None
    return float(value) if value else None
```

Also put a ceiling on any single wait (say 30–60 seconds) so a large attempt number can't make you sleep for an hour.

> **Try it:** In the practice editor, call your retry function with a fake `sleep=print` and a client that fails three times, and watch the delays grow.

## 4. Rate limits

Your organisation has limits, measured **per minute** and per model:

- **Requests per minute** (RPM)
- **Input tokens per minute** (ITPM)
- **Output tokens per minute** (OTPM)

Exceed any of them and you get a 429. Limits rise as your account's usage tier increases. Every response includes headers telling you where you stand (`anthropic-ratelimit-requests-remaining`, `anthropic-ratelimit-tokens-remaining` and friends), visible via the raw response:

```python
raw = client.messages.with_raw_response.create(
    model="claude-haiku-5-5", max_tokens=100,
    messages=[{"role": "user", "content": "Hi"}],
)
print(raw.headers.get("anthropic-ratelimit-requests-remaining"))
message = raw.parse()  # the normal Message object
```

How to stay under the limits:

- **Limit concurrency.** When processing a batch, don't fire 500 requests at once. Use an `asyncio.Semaphore` to allow, say, 5 in flight (you'll do this in the project).
- **Send fewer tokens.** Trim history, don't resend huge documents unnecessarily. Input tokens count against ITPM.
- **Back off on 429s**, as above.
- **Use the right model.** Haiku is cheaper, and limits are tracked per model.

## 5. Timeouts

The SDK's default timeout is **10 minutes**, generous because long generations take time. For an interactive app, you usually want to fail faster and show the user something:

```python
import httpx

client = anthropic.Anthropic(timeout=30.0)  # seconds, for every request
client = anthropic.Anthropic(timeout=httpx.Timeout(60.0, connect=5.0))  # finer control

response = client.with_options(timeout=10.0).messages.create(...)  # one request
```

A timed-out request raises `anthropic.APITimeoutError` (and the SDK retries it by default). Pick timeouts based on what you ask for: a 50-token classification should never take a minute; a 10,000-word report can. For long outputs, stream instead of raising the timeout, as covered in the streaming lesson.

## 6. Counting tokens before you send

`count_tokens` tells you exactly how many input tokens a request will use, without running the model and without cost:

```python
request = {
    "model": "claude-opus-5-5",
    "system": "You are a contract analyst.",
    "messages": [{"role": "user", "content": open("contract.txt").read()}],
}
count = client.messages.count_tokens(**request)
print(count.input_tokens)  # e.g. 48210
```

Use it to:

- **Reject or trim** inputs that are too big before sending them.
- **Estimate cost** up front: `input_tokens · price / 1,000,000`, plus an estimate for output.
- **Choose a strategy**: a short document goes in one call; a huge one gets split into chunks.

It accepts the same `system`, `messages` and `tools` arguments as `create`, so you can count exactly what you're about to send.

## 7. Tracking cost per request and per day

Every response's `usage` tells you what it cost. Record it, every time:

```python
from collections import defaultdict
from datetime import date

PRICES = {  # dollars per 1M tokens: (input, output)
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


class CostTracker:
    def __init__(self):
        self.requests = 0
        self.daily: defaultdict[date, float] = defaultdict(float)

    def record(self, model: str, usage, day: date | None = None) -> float:
        inp, out = PRICES[model]
        cost = (usage.input_tokens * inp + usage.output_tokens * out) / 1_000_000
        self.daily[day or date.today()] += cost
        self.requests += 1
        return cost


tracker = CostTracker()
response = client.messages.create(model="claude-haiku-5-5", max_tokens=500,
                                  messages=[{"role": "user", "content": "Hi"}])
print(f"${tracker.record('claude-haiku-5-5', response.usage):.6f}")
```

In production you'd write each request's cost to a database or log, along with the user, feature and model, so you can answer questions like "which feature costs the most?" and "which customer is using 80% of our budget?". You'll wire this up with proper tracing tools in the shipping section.

Practical guards:

- **Set a spend limit** in the Claude Console so a runaway bug can't exceed a monthly cap.
- **Cap loops** (`max_turns` on tool loops, `max_retries` on retries).
- **Cap `max_tokens`** to what the task needs.
- **Alert on anomalies**: a daily total twice yesterday's is worth a look.
- **Report cost per unit of value**: "₦4 per invoice processed" is how clients think.

## 8. Putting it together

A production-shaped call combines all of this:

```python
import logging
import anthropic

log = logging.getLogger("llm")
client = anthropic.Anthropic(max_retries=0, timeout=60.0)  # we handle retries ourselves
tracker = CostTracker()


def ask(prompt: str, model: str = "claude-haiku-5-5") -> str:
    request = {"model": model, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    try:
        response = call_with_retry(client, request, max_retries=3)
    except anthropic.APIStatusError as e:
        log.error("LLM call failed with %s: %s", e.status_code, e.message)
        raise
    cost = tracker.record(model, response.usage)
    log.info("id=%s in=%d out=%d cost=$%.5f", response.id,
             response.usage.input_tokens, response.usage.output_tokens, cost)
    return "".join(b.text for b in response.content if b.type == "text")
```

## Common mistakes

- **Retrying 400s.** They fail every time; fix the request.
- **Retrying instantly, with no backoff**, or all clients retrying in lockstep without jitter.
- **Unbounded retries or loops.** Always cap them.
- **Stacking retries**: your 5 retries × the SDK's 2 retries = up to 18 calls. Set `max_retries=0` on the client if you handle retries yourself.
- **Catching `Exception` and carrying on silently**, so failures never show up in logs.
- **No timeout on interactive requests**, leaving users waiting minutes.
- **Firing a whole batch concurrently** and getting a wall of 429s.
- **Not recording usage**, then being surprised by the invoice.

## Recap

- SDK errors: `APIConnectionError` (incl. `APITimeoutError`) and `APIStatusError` subclasses with `.status_code`.
- Retry 429, 5xx (incl. 529) and connection errors; never retry other 4xx.
- The SDK retries twice by default; tune with `max_retries` or `with_options`.
- Your own retries: exponential backoff (`base · 2ⁿ`) plus random jitter, capped attempts, injectable `sleep` for testing.
- Respect rate limits (RPM, ITPM, OTPM) by limiting concurrency and tokens.
- Set timeouts that fit the task; stream long outputs.
- `count_tokens` before sending; record `usage` cost after every call, per request and per day.
