# Your capstone product

Build **one** AI product, end to end, that a real business or a real group of people would pay for, and get **at least 3 real people** using it. It has a frontend or messaging channel, a FastAPI backend, Claude at its core (as a single call, a workflow, RAG or an agent: whichever is simplest and works), evals running in CI, cost tracking, and a public deployment. You finish with a 2-minute demo video and a case-study README.

This is the project you'll lead with in every pitch and interview in month 4. A deployed product with real users and measured results says more than any certificate: it shows you can pick a problem, make trade-offs, ship, and learn from users. It's also exactly what freelance clients are asking for: "an AI assistant for my business's WhatsApp", "a tool that tailors CVs", "turn our meeting notes into tasks".

Build it in **its own GitHub repository**, then paste the repo URL and your live URL into the fields below.

## Choosing what to build

Pick from your own user conversations (see *Choosing a problem worth three weeks*). If you're stuck, start from one of these and make it specific to real people you know:

- **Job-application assistant:** match a CV to a job post, tailor the CV and a cover letter without inventing experience, and track applications.
- **WhatsApp or email support bot for a local business:** answers from the business's own price list, FAQ and policies, and hands everything else to a human.
- **Meeting notes → action items:** from a transcript, a summary and action items with owners and deadlines, sent to the group.

## Week 9: spec, architecture and a walking skeleton

The goal of week 9 is the thinnest possible end-to-end path, **deployed**, so that everything after is improvement, not integration.

1. **Talk to at least five potential users.** Write notes. Pick the pain that came up most.
2. **Write the one-page spec** (`docs/spec.md`): user, job to be done, a numeric success metric, non-goals, 3-week scope. Get one potential user to read it and agree to try the product.
3. **Write the architecture** (`docs/architecture.md`): the pattern you chose and why, components, data model, API routes, every LLM call (purpose, model, input, output), a failure-mode table, a cost estimate per user per month, and a Mermaid sequence diagram of the main flow.
4. **Write your first ADRs** (`docs/adr/001-….md` onwards): at least the pattern choice and the model choice.
5. **Build the walking skeleton:** input from the real channel (web page, Telegram, or WhatsApp test number) → FastAPI → Claude → reply, with a `/health` route, settings from the environment, and the Claude client injected as a dependency.
6. **Deploy it** to Railway, Render, Fly.io or similar, with the Dockerfile and CI from the shipping lessons. Tracing on from day one.

**End of week 9:** you can send a message to a public URL or bot and get a reply from Claude. It may be a bad reply. That's fine.

## Week 10: core features, evals and first real users

1. **Build the core job** from your spec: the data (catalogue, CVs, transcripts), the prompts, structured output where you need it, retrieval only if the data doesn't fit in the prompt, and the "I don't know / hand over to a human" path.
2. **Make the channel production-safe:** verify webhook signatures, deduplicate by message id with a unique constraint, acknowledge fast and process after, map LLM errors to friendly fallbacks.
3. **Store conversations** with consent: a short privacy note, redaction of phone numbers and emails, pseudonymised user ids, token counts per message, and a way to delete a user's data.
4. **Build an eval set** of at least 20 cases from realistic inputs, with the grading that fits (exact checks for facts, an LLM judge with a rubric for open-ended output), and run it in **CI on every push**.
5. **Track cost:** cost per message and per user from the token counts, visible somewhere (a log line, an admin page, your tracing tool).
6. **Get your first real users** using it for real tasks. Sit with at least one of them while they use it.

**End of week 10:** at least two real people have used it; you have a list of what broke and what confused them, and your eval set runs in CI.

## Week 11: iterate, polish, launch and write it up

1. **Iterate from feedback:** fix wrong answers and confusing moments first. Every bug you fix becomes an eval case. Re-run evals after every prompt or model change.
2. **Reach at least 3 real users,** and measure your success metric from the logs.
3. **Polish for the public:** an onboarding message or empty state with examples, clear error messages, per-user rate limits, input caps, and a spend limit.
4. **Record a 2-minute demo video:** problem, the product doing the real job (including the failure path), one architecture slide, results.
5. **Write the case-study README:** problem, solution, architecture (diagram and ADR links), results with real numbers and how you measured them, what you learned, what you'd do next, and setup instructions.
6. **Announce it** on LinkedIn and/or X with the story, the demo and a specific call to action.

**Stop adding features at the start of week 11.** New ideas go in "What I'd do next".

## Requirements

1. **A real problem and real users:** a written spec, and at least 3 real people (not you) who used it for real tasks, more than once.
2. **Deployed:** a public URL or a bot anyone can message, running the same code as the repo's main branch.
3. **Architecture documented:** `docs/architecture.md` with a sequence diagram, failure modes and a cost estimate; at least 3 ADRs.
4. **Backend quality:** FastAPI, Pydantic models with limits, the Claude client as a dependency, LLM errors handled with friendly fallbacks, secrets only in environment variables, `.env.example` committed.
5. **Channel safety** if you use webhooks: signature or secret-token verification, idempotency on message ids, fast acknowledgement.
6. **Privacy:** a privacy note shown to users, consent before logging, redaction and pseudonymisation in logs, a delete path.
7. **Evals in CI:** at least 20 cases, including cases created from real user feedback, run by GitHub Actions on every push, failing the build below a threshold you choose and justify.
8. **Cost tracked:** token counts stored per message; cost per user per month reported in the README, compared with your week 9 estimate.
9. **Public-launch protection:** per-user rate limits and a spend cap.
10. **Offline tests:** unit and API tests that pass with no network and no API key (fake Claude client, `TestClient`).
11. **Demo video** of 2 minutes or less, linked at the top of the README.
12. **Case-study README** with real, measured results.

## Suggested repo layout

```
my-capstone/
├── README.md                 # the case study (+ setup at the end)
├── .env.example
├── Dockerfile
├── .github/workflows/ci.yml  # tests + evals on every push
├── docs/
│   ├── spec.md
│   ├── architecture.md
│   ├── privacy.md
│   └── adr/001-pattern.md, 002-model.md, 003-storage.md
├── app/
│   ├── main.py               # FastAPI app and routes
│   ├── config.py             # settings from the environment
│   ├── deps.py               # get_client, get_db, rate limiting
│   ├── core.py               # answer(user_id, text): the product logic
│   ├── channels/             # whatsapp.py, telegram.py, web.py: thin adapters
│   ├── store.py              # SQLite/Postgres access
│   └── privacy.py            # redact, pseudonym
├── frontend/                 # Streamlit app, static HTML, or Next.js
├── evals/
│   ├── cases.json
│   └── run_evals.py
└── tests/
```

## Definition of done

It's **deployed**, it has been **used by at least 3 real people**, its **evals run in CI**, its **cost is tracked** and reported, and there's a **demo video** and a case-study README that a stranger can understand in five minutes.
