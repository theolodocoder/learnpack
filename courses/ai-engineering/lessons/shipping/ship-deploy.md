# Deploying to a public URL

## Why this matters

A project on `localhost` is invisible to everyone deciding whether to hire you. A public URL that a client can `curl` in an interview, or a reviewer can click in a proposal, is worth more than any description of it. Platforms like Railway and Render take a Dockerfile from your GitHub repo and give you an HTTPS URL in a few minutes, with no servers to manage. This lesson walks through both, then covers what changes once strangers can reach your API.

## 1. What a platform does for you

Railway, Render, Fly.io, Google Cloud Run and similar "platform as a service" (PaaS) products all follow the same loop:

1. You connect a GitHub repo.
2. On every push to a chosen branch, the platform **builds** an image from your `Dockerfile` on its own machines.
3. It **starts** a container with your environment variables and a `PORT` variable it chooses.
4. It waits for the app to pass a **health check**, then **switches traffic** from the old version to the new one, which gives you zero-downtime deploys.
5. Its proxy **terminates HTTPS** on a public domain and forwards plain HTTP to your container's `$PORT`.

That's why the Dockerfile from *Docker for AI apps* listens on `0.0.0.0` and `${PORT:-8000}`: those are the two things every platform needs from you.

Before deploying, check locally that the image builds and runs with an unfamiliar port:

```bash
docker build -t docs-chat .
docker run --rm -e PORT=9123 -p 9123:9123 --env-file .env docs-chat
curl localhost:9123/health
```

If that works, the deploy will almost certainly work.

## 2. Deploying on Railway

Railway builds from your Dockerfile automatically when one named exactly `Dockerfile` is at the repo root.

**Create the service**

1. Sign in at railway.com with GitHub and create a **New Project → Deploy from GitHub repo**, then pick your repo. Railway detects the `Dockerfile` and starts a build.
2. The first deploy may fail because variables are missing. That's expected: your `Settings` model refuses to start without them, and the logs say exactly which ones.

**Add the database**

3. In the project canvas, click **+ New** (or press Cmd+K) and add **PostgreSQL**. For pgvector, the default Postgres template doesn't include extensions: deploy the **pgvector** template from Railway's template marketplace instead.
4. Railway's Postgres exposes `DATABASE_URL` (plus `PGHOST`, `PGUSER`, and so on). Your app connects over Railway's private network, so the database doesn't need a public address.

**Set variables**

5. Open your app service → **Variables**. Add `ANTHROPIC_API_KEY`, `APP_API_KEY`, `MODEL`, and `ENVIRONMENT=prod`. For the database, use a **reference variable** so it always matches the database service:

   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```

   (`Postgres` is the database service's name on the canvas; use whatever yours is called.)
6. Variable changes are **staged**: review them and click **Deploy** to apply. You can **seal** a variable so its value is never shown in the UI again.

**Health check and domain**

7. In the service **Settings**, set the **Healthcheck Path** to `/ready`. Railway calls it on each new deployment and only routes traffic once it returns 2xx. The default wait is 300 seconds. Railway does **not** keep polling after the deploy is live: use an uptime monitor for that.
8. Railway sends health checks with the hostname `healthcheck.railway.app`. If you use FastAPI's `TrustedHostMiddleware`, add that host to the allowed list or every deploy will fail its check.
9. In **Settings → Networking → Public Networking**, click **Generate Domain** to get an `*.up.railway.app` URL with HTTPS.

**Logs**

10. Click a deployment to see its **build logs** and **deploy logs** (your app's stdout). The JSON logs from *Observability for LLM apps* make these searchable. The Railway CLI can stream them too: `railway logs`.

## 3. Deploying on Render

**Create the service**

1. On render.com, click **New → Web Service**, connect GitHub and choose the repo.
2. Set **Language** to **Docker**. Render builds the root `Dockerfile` (change *Dockerfile Path* if yours is elsewhere) using BuildKit on every deploy.
3. Choose an instance type. The free type works for demos, with limits covered in section 5.
4. Under **Environment Variables**, add `ANTHROPIC_API_KEY`, `APP_API_KEY`, `MODEL`, `ENVIRONMENT=prod`. Then **Deploy**.

**Port**

Render sets `PORT` (default `10000`) and routes traffic to it. Your `${PORT:-8000}` handles that with no changes.

**Add the database**

5. **New → Postgres**, in the same region as the web service. When it's ready, copy its **Internal Database URL** into the web service's `DATABASE_URL` variable. Internal URLs work only between Render services in the same region and are faster than the external one.
6. Render Postgres supports pgvector, but you enable it: run `CREATE EXTENSION vector;` once (open a `psql` session from the database's page), or let your app's startup run `CREATE EXTENSION IF NOT EXISTS vector;`.

**Health check, domain, logs**

7. Service **Settings → Health Checks**: set the path to `/ready`. Render treats a 2xx or 3xx answer within five seconds as healthy. During a deploy it waits for the new instance to pass before switching traffic; if that doesn't happen within 15 minutes, the deploy is cancelled and the old version keeps serving. While running, an instance failing for 15 seconds stops getting traffic, and after 60 seconds Render restarts it.
8. Your URL is `https://<service-name>.onrender.com`. The **Logs** tab streams stdout.

## 4. Custom domains

A custom domain (`api.yourname.dev`) looks professional on a portfolio and costs about $10–15 a year at any registrar.

- **Railway:** service **Settings → Networking → Custom Domain**. Railway shows a `CNAME` record and a `TXT` verification record; add **both** at your DNS provider.
- **Render:** service **Settings → Custom Domains → + Add Custom Domain**. Point a `CNAME` for your subdomain at your `onrender.com` address, then click **Verify**.

Both platforms issue and renew the HTTPS certificate automatically once DNS resolves. DNS changes can take minutes to hours to spread. Use a subdomain (`api.`) rather than the bare domain: root domains can't have a `CNAME`, which needs extra steps.

## 5. What it costs

Hosting is usually cheaper than the model calls it serves. Prices change, so check each pricing page before you commit.

- **Railway:** new accounts get a one-time trial credit. There's a Free plan with $1 of credit a month, and the Hobby plan is $5 a month including $5 of usage. Usage is billed by the CPU, memory and network you actually use, so a small API and database idle most of the day fits in Hobby.
- **Render:** the free web service **spins down after 15 minutes without traffic**, and the next request waits about a minute while it starts again. Fine for a demo, bad for a live client. Free Postgres databases **expire 30 days after creation** (with a 14-day grace period to upgrade), and you get one per workspace. Paid instances don't sleep.
- **Claude:** at Haiku 5.5 prices ($0.10 in / $0.50 out per million tokens), a RAG question with 3,000 input and 300 output tokens costs about $0.00045, roughly 2,000 questions per dollar. The same on Opus 5.5 ($4 / $20) is about $0.018. Set a spend limit in the Claude Console before your URL is public.

## 6. What changes when your app is public

Anyone can now send your API anything. Authentication and rate limits get their own lesson (*Reliability, auth and cost control*). Three other guards belong in every public app.

### CORS

Browsers block JavaScript on one site (origin) from reading responses from another, unless the server says it's allowed. That permission is **CORS** (Cross-Origin Resource Sharing). A browser sends a **preflight** `OPTIONS` request with an `Origin` header first; your server replies with `Access-Control-Allow-Origin` if that origin is allowed.

CORS only matters for browsers. `curl`, Python scripts and server-to-server calls ignore it, which is why your API works from `curl` and "mysteriously" fails from a front end.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com", "http://localhost:3000"],   # from settings, per environment
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

List exact origins (scheme + host + port, no trailing slash). `allow_origins=["*"]` lets any website call your API from its visitors' browsers. For an API that spends money on every call, that's an open door. Read the list from an environment variable so development and production differ.

### Request size limits

FastAPI will happily read a 500 MB body into memory. Validation catches long *fields* (`Field(max_length=4000)`), but only after the whole body is read. Reject oversized requests early, from the `Content-Length` header:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

MAX_BODY = 1_000_000  # 1 MB; uploads may need more


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length is not None:
        if not length.isdigit():
            return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
        if int(length) > MAX_BODY:
            return JSONResponse({"detail": "Request body too large"}, status_code=413)
    return await call_next(request)
```

Also cap what reaches the model: maximum question length, maximum `k`, maximum upload size, maximum conversation turns. Every limit is a cost limit.

### Timeouts

Every slow thing needs a timeout, or one stuck call ties up a worker indefinitely:

- **The Claude client:** `AsyncAnthropic(timeout=60.0, max_retries=2)`. The SDK default allows up to ten minutes, which is right for batch jobs and wrong for a person waiting.
- **Other HTTP calls:** `httpx.AsyncClient(timeout=10.0)`.
- **Database:** a pool connection timeout (`pool.connection(timeout=2)`) and a statement timeout for queries.
- **The whole request:** an overall budget so the user gets an answer, even an error, in reasonable time:

  ```python
  import asyncio
  from fastapi import HTTPException

  async def answer_with_budget(question: str) -> str:
      try:
          async with asyncio.timeout(45):
              return await answer(question)
      except TimeoutError:
          raise HTTPException(504, "The answer took too long. Please try again.")
  ```

- **Long generations:** stream them (*Serving Claude from FastAPI*). Streaming sends the first bytes in about a second, so proxies and browsers don't give up on a quiet connection.

### Two smaller things

- **Disable the docs in production** if your API isn't public-facing: `FastAPI(docs_url=None, redoc_url=None)` when `ENVIRONMENT=prod`. Or keep them: they make a nice demo. Decide on purpose.
- **Proxy headers:** behind a platform proxy, `request.client.host` is the proxy's address. Uvicorn's `--proxy-headers` option with `--forwarded-allow-ips` set to the proxy's addresses reads the real client IP from `X-Forwarded-For`. Only trust that header from your platform's proxy, because clients can set it to anything.

## Common mistakes

- **App listens on `127.0.0.1` or a fixed port.** The deploy builds, then fails its health check. Use `0.0.0.0` and `$PORT`.
- **Health check path not set, or pointing at a route that needs an API key.** The platform gets 401 and marks the deploy unhealthy.
- **`DATABASE_URL` pasted as a fixed string** instead of a Railway reference or Render's internal URL. It breaks when credentials rotate and uses the slower public route.
- **Forgetting `CREATE EXTENSION vector`** on a fresh production database. Run it at startup with `IF NOT EXISTS`.
- **`allow_origins=["*"]`** on a paid API.
- **No spend limit** on the Claude key used in production.
- **Demoing on a free Render instance that just went to sleep.** Hit it a minute before the call, or use a paid instance.

## Recap

- Platforms build your Dockerfile on each push, inject `PORT` and your variables, wait for a health check, then switch traffic, all behind HTTPS.
- Railway: deploy from GitHub, add Postgres (or the pgvector template), set variables (`${{Postgres.DATABASE_URL}}`), set the healthcheck path, generate a domain.
- Render: New Web Service with Language **Docker**, add Postgres in the same region, use the internal URL, enable `vector`, set the health check path.
- Custom domains are a `CNAME` (plus Railway's `TXT`); HTTPS certificates are automatic.
- Know the free-tier limits (Render sleeps after 15 minutes, free Postgres expires after 30 days) and set a Claude spend limit.
- Public APIs need exact-origin CORS, request size limits, and timeouts at every layer.
