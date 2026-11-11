# Observability for LLM apps

## Why this matters

Once your app is public, you'll get messages like "it gave a weird answer yesterday" and "why is the bill $40 this week?". Without records, you can only guess. An LLM app has failure modes ordinary backends don't: the call succeeded but the answer was wrong, one user's 50-turn conversation costs more than everyone else's together, or the model got slower this afternoon. Observability means recording enough about every request and every model call that you can answer those questions from data: what was asked, what the model saw and said, how long it took, and what it cost.

## 1. Logs, metrics, traces

Three kinds of telemetry, each for a different question:

- **Logs:** individual events with details. "Request abc123 failed: Claude returned 529." For debugging one request.
- **Metrics:** numbers aggregated over time. "Error rate 2.1% in the last 5 minutes; p95 latency 4.2 s; $3.10 spent today." For dashboards and alerts.
- **Traces:** the tree of steps inside one request, with timings. "`/ask` took 3.8 s: embed 0.2 s, search 0.05 s, Claude 3.5 s (2,900 tokens in, 310 out, $0.0004)." For finding where time and money go.

Logs and traces carry a shared **request id**, so you can jump from a log line to the full trace of the same request.

## 2. Structured logs

`print("user asked", question)` produces text a human can read and a machine can't search. Platforms like Railway and Render collect your stdout, and log tools can filter and aggregate **JSON** lines by field: `level = "ERROR" and model = "claude-opus-5-5"`. So log one JSON object per line.

Python's `logging` module separates *what* is logged (a `LogRecord`) from *how* it's printed (a `Formatter`). Write a formatter that outputs JSON:

```python
import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
_STANDARD = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        data.update({k: v for k, v in vars(record).items() if k not in _STANDARD})  # fields from extra=
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()          # stdout/stderr: the platform collects it
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)


setup_logging()
log = logging.getLogger("app")
log.info("answered question", extra={"model": "claude-haiku-5-5", "input_tokens": 2900, "latency_ms": 3512})
# {"time": "2026-11-11T09:30:01.123+00:00", "level": "INFO", "logger": "app", "message": "answered question",
#  "request_id": "-", "model": "claude-haiku-5-5", "input_tokens": 2900, "latency_ms": 3512}
```

- Keep `message` a fixed phrase ("answered question") and put the variable parts in `extra=` fields. Then you can count "answered question" events and graph `latency_ms`.
- `log.exception("...")` inside an `except` block adds the traceback as `exc_info`.
- `default=str` stops an odd value (a `datetime`, a `Path`) from crashing your logging.

### Request ids with a context variable

Every log line written while handling one request should carry that request's id. Passing it through every function is tedious. A `ContextVar` holds a value per request (per asyncio task), so a middleware can set it once:

```python
import uuid

from fastapi import FastAPI, Request

app = FastAPI()


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response
```

- Reusing an incoming `X-Request-ID` lets a front end or another service tie its logs to yours.
- Returning it in the response lets a user report "request id 3f9a…" with their bug. Include it in error bodies too.
- `reset(token)` restores the previous value, so ids can't leak between requests.

### What not to log

- **Secrets:** API keys, `Authorization` headers, the settings object (use `SecretStr`).
- **Full prompts and answers in plain logs,** if users may send personal data. Logs are kept for a long time, copied to many tools and read by anyone with platform access. Log sizes and ids in logs; keep full content in a tracing tool with access control and a retention period, and say so in your privacy notice.

> **Try it:** The *JSON logs with a request id* exercise builds the formatter and middleware. Run it and look at the line printed for `/ping`.

## 3. Tracing LLM calls

For each model call, record:

| Field | Why |
|---|---|
| name / step (`"answer"`, `"rewrite_query"`, `"judge"`) | which part of your app made it |
| model | cost and behaviour differ per model |
| input and output (or a reference to them) | debugging wrong answers |
| `input_tokens`, `output_tokens`, cache tokens | cost, and spotting runaway prompts |
| cost in USD | the number your client cares about |
| latency (ms) | user experience, and spotting slow steps |
| `stop_reason` | `max_tokens` means answers are being cut off |
| error and status code | 429s and 529s versus your own bugs |
| request id, user id, prompt version | joining it to everything else |

A small wrapper captures most of it. Inject the clock so it's testable:

```python
import time

PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00),
          "claude-haiku-5-5": (0.10, 0.50)}   # USD per 1M tokens (input, output)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    if model not in PRICES:
        return None
    p_in, p_out = PRICES[model]
    return round((input_tokens * p_in + output_tokens * p_out) / 1_000_000, 6)


class Tracer:
    def __init__(self, clock=time.perf_counter):
        self.clock = clock
        self.records: list[dict] = []

    def create(self, client, name: str, **kwargs):
        record = {"name": name, "model": kwargs.get("model"), "input_tokens": 0, "output_tokens": 0,
                  "cost_usd": None, "latency_ms": 0.0, "error": None}
        start = self.clock()
        try:
            response = client.messages.create(**kwargs)
        except Exception as e:
            record["error"] = f"{type(e).__name__} ({getattr(e, 'status_code', None)})"
            raise
        else:
            record["input_tokens"] = response.usage.input_tokens
            record["output_tokens"] = response.usage.output_tokens
            record["cost_usd"] = cost_usd(record["model"], record["input_tokens"], record["output_tokens"])
            return response
        finally:
            record["latency_ms"] = round((self.clock() - start) * 1000, 3)
            self.records.append(record)
```

`try` / `except` / `else` / `finally` does the bookkeeping: `else` runs only on success, `finally` always runs, so failed calls are recorded with their latency, and the error is still re-raised for your error mapping.

In a real app, the "record" goes to three places: a JSON log line (`log.info("llm call", extra=record)`), a tracing tool, and your metrics. In the exercise it's a list, which is enough to test.

> **Note:** Use `response.usage` for tokens, never your own estimate. With prompt caching (next lesson) there are two more fields, `cache_creation_input_tokens` and `cache_read_input_tokens`, billed at different rates. A complete cost function includes them.

## 4. Langfuse: traces, observations, scores

You could build a trace viewer yourself, but tools exist for exactly this. **Langfuse** is an open-source LLM observability platform: use the hosted cloud version (with a free tier) or self-host it with Docker. Similar tools include LangSmith, Arize Phoenix, Helicone and Braintrust. The concepts transfer.

Langfuse's data model:

- **Trace:** one end-to-end request, e.g. one `/ask` call. It has a name, input, output, a `user_id`, a `session_id` (to group a conversation's turns), tags and metadata.
- **Observations:** the steps inside a trace, nested as a tree. Three kinds matter here:
  - **Span:** a unit of work with a duration: "retrieve", "rerank", a tool call.
  - **Generation:** a span that is an LLM call. It has extra fields for the model, token usage and cost, which Langfuse aggregates into cost dashboards.
  - **Event:** a point-in-time marker with no duration.
- **Scores:** numbers or labels attached to a trace or observation: a user's thumbs up/down, an LLM-as-judge rating, a "had citations" check. Scores turn traces into an evaluation dataset you can filter ("show me low-scored answers from yesterday").

Langfuse isn't installed in your exercise environment, and its SDK changes between major versions, so treat this as an illustration of the shape and check the docs for the version you install. With the Python SDK, the integration looks like this:

```python
# pip install langfuse ; env: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
from langfuse import get_client, observe, propagate_attributes

langfuse = get_client()


@observe(name="retrieve")                       # a span, timed automatically, nested under the trace
def retrieve(question: str) -> list[str]:
    return store.search(embed(question), k=5)


def generate(question: str, chunks: list[str]) -> str:
    with langfuse.start_as_current_observation(as_type="generation", name="answer",
                                               model="claude-haiku-5-5",
                                               input={"question": question, "chunks": len(chunks)}) as gen:
        response = client.messages.create(model="claude-haiku-5-5", max_tokens=1024,
                                          messages=build_messages(question, chunks))
        answer = "".join(b.text for b in response.content if b.type == "text")
        gen.update(output=answer, usage_details={"input_tokens": response.usage.input_tokens,
                                                 "output_tokens": response.usage.output_tokens})
        return answer


@observe(name="ask")                            # the outermost observed function becomes the trace
def ask(question: str, user_id: str, session_id: str) -> str:
    with propagate_attributes(user_id=user_id, session_id=session_id):
        answer = generate(question, retrieve(question))
    langfuse.score_current_trace(name="has_citation", value=1.0 if "[" in answer else 0.0)
    return answer
```

- The decorator and the context manager create observations **nested by call order**, using context variables, the same mechanism as your request id.
- `usage_details` gives Langfuse the token counts; with a known model name it computes cost for you, and you can also send your own cost.
- `score_current_trace` attaches a score. User feedback arrives later, so you'd store the trace id with the answer and score it when the thumbs-up comes in, with `langfuse.create_score(name=..., value=..., trace_id=...)`.
- The SDK sends data in the **background**, batched, so tracing doesn't slow requests. In short-lived scripts (an eval run, a CLI) call `langfuse.flush()` before exiting or the last events are lost.
- Langfuse also has integrations that wrap common SDKs and frameworks automatically, built on **OpenTelemetry**, the vendor-neutral standard for traces. Anything that emits OpenTelemetry can send traces to Langfuse.

## 5. Dashboards: the numbers to watch

Whether you use Langfuse's dashboards, your platform's metrics, or a notebook over exported logs, these are the core numbers for an LLM app:

- **Traffic:** requests per minute, by route.
- **Errors:** error rate (5xx responses ÷ all responses), split by cause: upstream 429/529, timeouts, your bugs.
- **Latency:** p50 and p95 per route and per step, plus time to first token for streaming.
- **Tokens and cost:** per day, per model, per route, and **per request**, the number you need to price your product.
- **Cache hit rate** for your response cache and Claude's prompt cache.
- **Quality:** average eval or user-feedback score over time.

Use **percentiles, not averages**, for latency. If 95 requests take 1 s and 5 take 30 s, the mean is 2.45 s, which describes nobody. p50 (the median) is 1 s; p95 shows the slow tail your unhappy users live in:

```python
import statistics

latencies = [1.0] * 95 + [30.0] * 5
print(statistics.mean(latencies))                     # 2.45
cuts = statistics.quantiles(latencies, n=100)         # 99 cut points
print(cuts[49], cuts[94])                             # 1.0 28.55  (p50, p95)
```

Cost per request matters for the same reason: a few long conversations can dominate the bill. Group cost by `user_id` and look at the top ten.

## 6. Alerting

A dashboard nobody looks at doesn't help at 2am. Alerts should fire on **symptoms users feel or money you lose**, and stay quiet otherwise:

- **Error rate** above, say, 5% over 5 minutes, with a minimum request count (one failure out of two requests is 50%, and not an incident).
- **p95 latency** above your target for 10 minutes.
- **Spend** per day above a budget. Also set a hard **spend limit** in the Claude Console: an alert tells you; a limit stops it.
- **The app is down:** an external uptime monitor (UptimeRobot, Better Stack and similar have free tiers) calls `/health` every minute and emails you when it fails. Remember that Railway only checks health during deploys.

The core of an error-rate alert is a few lines over recent records:

```python
def should_alert(records: list[dict], now: float, window_s: float = 300,
                 max_error_rate: float = 0.05, min_requests: int = 20) -> bool:
    recent = [r for r in records if now - r["time"] <= window_s]
    if len(recent) < min_requests:
        return False
    errors = sum(1 for r in recent if r["status"] >= 500)
    return errors / len(recent) > max_error_rate
```

Each alert should say what's wrong and link to the dashboard. If an alert fires and you do nothing, change or delete it; noisy alerts get muted, and then the real one gets missed.

## Common mistakes

- **Plain-text logs** you can't filter or aggregate. Log JSON with fixed messages and fields in `extra`.
- **No request id,** so you can't connect a user's complaint to log lines.
- **Logging secrets or personal data** into long-lived logs.
- **Estimating tokens** instead of reading `response.usage`, or forgetting cache token fields when computing cost.
- **Averages for latency.** Use p50 and p95.
- **Not flushing** the tracing client at the end of scripts and eval runs.
- **Alerts on every single error,** or with no minimum request count, until everyone ignores them.

## Recap

- Logs explain single events, metrics show trends, traces break one request into timed steps; a request id links them.
- Log one JSON object per line with a `JsonFormatter`; a middleware puts a request id in a `ContextVar` and in the response header.
- For every LLM call record model, input/output, tokens, cost, latency, stop reason and errors, from `response.usage`.
- Langfuse models this as traces made of spans and generations, with scores attached; data is sent in the background, so flush in scripts.
- Dashboard traffic, error rate, p50/p95 latency, cost per day and per request, cache hit rate, and quality scores.
- Alert on sustained error rates, latency and spend, use an external uptime monitor, and set a hard spend limit.
