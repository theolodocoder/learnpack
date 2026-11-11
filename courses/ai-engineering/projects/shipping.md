# Ship it: production-ready and public

You've built three AI systems: a **document extractor**, a **chat-with-your-docs API**, and an **agent with evals**. Right now they run on your laptop. This project turns all three into services a stranger could use and a client could trust: containerised, deployed to public URLs, tested and evaluated on every push, traced with cost tracking, protected by auth and rate limits, and documented well enough that someone can understand each one in two minutes.

This is the step that separates "I followed a tutorial" from "I ship". When a client or interviewer opens your GitHub, they should see three repos that each have a green CI badge, a live URL, a demo GIF, an architecture diagram and a cost-per-request figure. That's the portfolio you'll use to win work next month.

Work in **the three existing repositories**. Paste the URL of the repo you consider your best (usually the RAG API) and its live URL in the fields below, and link the other two from its README.

## Requirements (for each of the three projects)

1. **Config:** every setting comes from environment variables through a validated `Settings` model loaded at startup; a missing variable stops the app with a clear message. `.env` is git-ignored and `.env.example` is committed.
2. **Health:** `GET /health` (liveness, no dependencies) and, where there's a database, `GET /ready` (returns 503 when the database is unreachable). Both open, no API key.
3. **Docker:** a `Dockerfile` (uv, slim base, dependencies before code, non-root user, `0.0.0.0` and `${PORT:-8000}`), a `.dockerignore` that excludes `.env`, `.venv` and `.git`, and a `docker-compose.yml` where the app needs Postgres. `docker compose up --build` starts a working local copy.
4. **Deployed** on Railway or Render (or similar) with a public HTTPS URL, its health check path set, secrets only in the platform's variables, and a production Anthropic key with a spend limit.
5. **CI:** a GitHub Actions workflow that runs `pytest` and an offline eval suite with a pass-rate gate (nonzero exit below your threshold) on every push and pull request, plus a job that builds the Docker image. `main` requires these checks to pass.
6. **Observability:** JSON logs with a request id (returned as `X-Request-ID`), and every LLM call traced with model, tokens, cost, latency and errors, in Langfuse (or a similar tool) or at least in your JSON logs. An external uptime monitor pings `/health`.
7. **Auth and limits:** per-client API keys stored as SHA-256 hashes and checked with `hmac.compare_digest`; a token-bucket rate limit returning 429 with `Retry-After`; CORS limited to your own front-end origins; request size limits and timeouts.
8. **Cost controls:** prompt caching on the stable part of each prompt (verify with `cache_read_input_tokens`), a response cache where repeat questions are likely, and a measured **cost per request** in the README.
9. **README** with: a one-paragraph summary, the live URL and a working `curl` example, a demo GIF, an architecture diagram, setup with Docker, the eval results and threshold, cost per request, and known limitations.

## Suggested additions to each repo

```
your-project/
├── .dockerignore
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml                 # tests + offline evals + gate + docker build
│       └── live-evals.yml         # optional: manual/scheduled run against the real model
├── Dockerfile
├── docker-compose.yml             # app + pgvector, where needed
├── app/
│   ├── config.py                  # Settings + load_settings(os.environ)
│   ├── security.py                # hash_api_key, require_client, TokenBucket, rate_limit
│   ├── observability.py           # JsonFormatter, request-id middleware, LLM tracing
│   └── cache.py                   # cache_key, TTLCache (or Redis)
├── evals/
│   ├── run_offline.py             # writes results.json
│   └── gate.py                    # exit 1 below the threshold
└── docs/
    ├── demo.gif
    └── architecture.png           # or a Mermaid diagram in the README
```

Copy the pieces you wrote in this section's exercises into these files. They were designed to be reused.

## Build plan

### Step 1: one project, end to end

Start with the chat-with-your-docs API: it has the most moving parts (Postgres, embeddings, Claude). Get it all the way through steps 2–8 first, then repeat for the other two, which will take a fraction of the time.

### Step 2: config and health

Replace scattered `os.environ` reads with `Settings` and `load_settings(os.environ)` in the lifespan. Add `/health` and `/ready`. Delete `.env` from your shell for a moment and confirm the app refuses to start and names the missing variables.

### Step 3: Docker locally

Write the `Dockerfile` and `.dockerignore` from *Docker for AI apps*. Check:

```bash
docker build -t docs-chat .
docker run --rm -e PORT=9123 -p 9123:9123 --env-file .env docs-chat
curl localhost:9123/health
docker run --rm docs-chat whoami          # must not be root
```

Then `docker-compose.yml` with `pgvector/pgvector:pg17`, and `docker compose up --build`. Ingest a sample document and ask a question through the containerised app.

### Step 4: CI

Add `.github/workflows/ci.yml` from *CI with GitHub Actions: tests and eval gates*. Write `evals/run_offline.py`: retrieval recall@k on your golden set with a deterministic embedder or committed embeddings, plus checks over recorded model outputs (citations parse, refusals happen when they should). Add the gate, push, and watch it go green. Then break something on purpose in a branch, open a pull request, and confirm the check goes red and blocks the merge once you've made it required.

### Step 5: deploy

Follow *Deploying to a public URL* for Railway or Render: database (with pgvector), variables (reference variables or the internal URL), health check path, generated domain. Ingest your sample documents in production and `curl` the live URL. Set a spend limit on the production key.

### Step 6: observability

Add the JSON formatter and request-id middleware. Wrap every Claude call so it records model, tokens (including cache tokens), cost, latency and errors. Sign up for Langfuse Cloud's free tier (or self-host it) and send traces with generations nested under each request, with `user_id` set to the API-key owner. Add an uptime monitor on `/health`.

### Step 7: auth, limits and cost

- Create an `api_keys` table and a small script that generates a key, prints it once, and stores the hash.
- Add `require_client` and `rate_limit` dependencies to every route except health checks.
- Restrict CORS to your front-end origins; add the body size middleware and timeouts.
- Restructure prompts so the stable part comes first, add `cache_control`, and confirm `cache_read_input_tokens > 0` on a second call within five minutes.
- Add a response cache for exact repeats.
- Measure: run 20 typical requests, sum the cost from your traces, and divide. Put the number in the README with the model used.

### Step 8: the README

- **Demo GIF:** record 15–30 seconds of the app working (a terminal running `curl`, or a small web page), with a screen recorder such as macOS's built-in one (Cmd+Shift+5) and convert to a GIF (for example with `ffmpeg` or an online converter). Keep it under a few MB.
- **Architecture diagram:** boxes and arrows for client → API → (Postgres/pgvector, embeddings, Claude, Langfuse). Draw it in Excalidraw or write it as a Mermaid code block, which GitHub renders:

  ````markdown
  ```mermaid
  flowchart LR
      C[Client] -->|X-API-Key| A[FastAPI on Railway]
      A --> P[(Postgres + pgvector)]
      A --> E[Embeddings API]
      A --> L[Claude API]
      A -.traces.-> F[Langfuse]
  ```
  ````

- Then: live URL, `curl` example, local setup (`cp .env.example .env`, `docker compose up --build`), eval results and threshold, cost per request, the CI badge, and an honest "Limitations" section.

### Step 9: repeat for the extractor and the agent

The extractor probably needs no database: skip compose and `/ready`. For the agent, trace each tool call as a span under the run's trace, put a cap on steps and tokens per run, and make the eval gate cover tool-selection accuracy on recorded runs.

## Stretch goals

- **Redis** for rate limits and the response cache, so you can run two instances.
- **Live evals** on a weekly schedule with a CI-only key, and a dashboard of eval score over time.
- **Per-client token quotas** with a `GET /usage` endpoint showing each client their spend.
- **Model fallback** (Opus → Sonnet → Haiku on 529) with evals run against each fallback model.
- **Preview environments:** Railway and Render can deploy each pull request to its own temporary URL.
- **A custom domain** (`api.yourname.dev`) for all three services.

## Submitting

Paste your best repo's URL and its live URL below, link the other two repos and live URLs from that README, and tick each checklist item as you finish it.
