# A portfolio that gets you hired

## Why this matters

Clients and hiring managers don't read your code first. They spend 30–90 seconds on your GitHub profile, a README and maybe a demo video, and in that time they decide whether to reply. You have already built a document extractor, a RAG API, an agent with evals and a capstone with real users. That's more than most applicants have. The work now is to make that evidence **fast to see and easy to believe**.

A good portfolio answers three questions in under a minute:

1. **What can this person build?** (demos, not claims)
2. **Does it actually work?** (live links, numbers, tests, evals)
3. **Would I trust them with my problem?** (clear writing, honest trade-offs, cost awareness)

## 1. The GitHub profile: your shop window

### The profile README

GitHub shows a special README at the top of your profile page. To create it, make a **public repository with exactly the same name as your username** (if you're `ada-obi`, the repo is `ada-obi/ada-obi`) and put a `README.md` at its root. Whatever is in that file appears above your pinned repos.

Keep it short. A visitor should get the point from the first three lines:

```markdown
# Ada Obi: AI engineer (LLM apps, RAG, agents)

I build LLM-powered products that ship: document extraction, chat-with-your-docs, and agents with evals.
CS student in Lagos. Open to freelance projects and AI engineering internships.

**Selected work**
- **DocPilot**: chat with your company docs. FastAPI + pgvector + Claude. 0.87 answer accuracy on a 60-question eval set, ~$0.002 per answer. [Demo](https://...) · [Code](https://...)
- **InvoiceX**: invoices and CVs → validated JSON. 120 docs in 2 minutes, $0.004 per document. [2-min video](https://...)
- **TriageAgent**: support-ticket agent with tool calls, traced and evaluated. [Write-up](https://...)

**Contact:** ada@example.com · [LinkedIn](https://...) · [X](https://...) · [Portfolio](https://...)
```

What this does well:

- **One-line positioning** in words a client searches for ("RAG", "document extraction", "agents"), not "passionate developer".
- **Each project has a number.** Accuracy, cost, speed, users. Numbers make a claim checkable.
- **Links go to proof**: a demo, a video or the code.
- **A clear ask**: freelance work and internships.

Skip the things that add noise: animated typing banners, ten badge rows for every language you've touched, GitHub stats cards and streak counters. They make a profile look like a template, and they push your real work below the fold.

### Pinned repositories

You can pin up to **six** repositories (or gists) to your profile. Pin your best four or five, in this order:

1. The capstone (real users is your strongest signal)
2. The RAG API
3. The agent with evals
4. The document extractor
5. Optionally, one small, polished tool or library

Unpin course exercises, forks and half-finished experiments. They're not hidden from people who look, but they shouldn't be the first thing anyone sees. Give every pinned repo a one-line **description** and a few **topics** (`rag`, `llm`, `fastapi`, `anthropic`) in the repo's About box: those show on the profile card.

> **Try it:** Open your own GitHub profile in a private browser window, start a 30-second timer, and look at it as a stranger. When the timer stops, write down what you'd say this person does. If it isn't "builds LLM products", fix the top of your profile README first.

## 2. The project README formula

Every pinned repo gets a README with the same five parts, in this order. Readers stop early, so the most convincing things go first.

1. **The problem** (2–3 sentences, in the user's language)
2. **The demo** (a GIF or short video right below the title)
3. **The architecture** (a small diagram and a few lines on why)
4. **Results with numbers** (evals, cost, latency, usage)
5. **How to run it** (copy-paste commands that actually work)

Here's a full skeleton:

````markdown
# DocPilot: ask questions about your company's documents

Small teams keep policies, contracts and SOPs in dozens of PDFs. Finding one answer means
searching folders and reading pages. DocPilot answers questions from those documents in
seconds and cites the page it used, so answers can be checked.

![Demo: asking about the leave policy and getting a cited answer](docs/demo.gif)

**Live demo:** https://docpilot.example.com · **2-min walkthrough:** https://loom.com/share/...

## How it works

```
upload → split into ~500-token chunks → embed → Postgres + pgvector
question → embed → hybrid search (vector + keyword, RRF) → top 5 chunks → Claude → answer with citations
```

- FastAPI service, Dockerised, deployed on Fly.io
- Hybrid search because exact policy names ("Form HR-12") were missed by vector search alone
- Every request is traced (inputs, retrieved chunks, tokens, latency)

## Results

| Metric | Value | How measured |
|---|---|---|
| Answer accuracy | 0.87 | 60 hand-written questions, graded by an LLM judge + spot-checked |
| Retrieval hit rate @5 | 0.93 | Correct chunk in top 5 |
| Median latency | 1.8 s | p50 over 500 traced requests |
| Cost per answer | ~$0.002 | Haiku 5.5 for answers, tokens from usage logs |

Biggest improvement: adding keyword search raised hit rate from 0.78 to 0.93.

## Run it locally

```bash
git clone https://github.com/ada-obi/docpilot && cd docpilot
cp .env.example .env          # add ANTHROPIC_API_KEY
docker compose up --build
open http://localhost:8000/docs
```

## Limitations and next steps
- Scanned PDFs need OCR first (not supported yet)
- Eval set is small; growing it from real user questions
````

Notice the **Limitations** section. It looks like a weakness but it's a strength: it shows you understand your own system. Engineers who list what doesn't work yet are more believable about what does.

### The demo GIF

Put a 10–20 second GIF right under the title. It should show **one complete action**: the user asks a question, the answer streams in, the citation appears. No intro, no logo, no menus.

Practical tips:

- Record at a normal window size and crop to the interesting part. Big text, short clip.
- Keep the file under a few MB so the README loads quickly. Tools like ScreenToGif (Windows), Kap (macOS) or Peek (Linux) export GIFs directly; or record an MP4 and convert it.
- Put it in a `docs/` folder in the repo and reference it with a relative path.

### Architecture: show decisions, not boxes

A diagram with "Frontend → Backend → Database" says nothing. A diagram plus **why** says a lot: "Hybrid search because vector search missed exact form names." Each "because" is evidence that you made a decision and checked it. Plain text diagrams in a code block are fine and render everywhere.

## 3. Evals and costs: proof of engineering maturity

Most AI portfolios are demos: it worked when the author tried it. What separates an engineer from a tinkerer is **measurement**. You already have the pieces from earlier sections: eval sets, traces and token usage. Put them up front.

What to show:

- **An eval table**: the metric, the score, the size of the eval set and how it was graded.
- **A before/after**: "Changing chunk size from 1,000 to 500 tokens raised accuracy from 0.74 to 0.87." One improvement story beats ten features.
- **Cost per unit of work**: per document, per answer, per conversation. Clients think in "how much will this cost me per month?", so give them the unit cost.
- **Latency**: median (p50) and slow-case (p95) times.

Computing cost per unit is a few lines over your usage logs. If your traces are a list of records:

```python
PRICES = {"claude-haiku-5-5": (0.10, 0.50), "claude-opus-5-5": (4.00, 20.00)}  # $ per 1M tokens (in, out)

calls = [
    {"model": "claude-haiku-5-5", "input_tokens": 3_200, "output_tokens": 410},
    {"model": "claude-haiku-5-5", "input_tokens": 2_900, "output_tokens": 380},
    {"model": "claude-opus-5-5", "input_tokens": 1_100, "output_tokens": 250},
]

def cost(c):
    i, o = PRICES[c["model"]]
    return (c["input_tokens"] * i + c["output_tokens"] * o) / 1_000_000

total = sum(cost(c) for c in calls)
print(f"total ${total:.4f}, per call ${total / len(calls):.4f}")
# total $0.0104, per call $0.0035
```

> **Note:** Be honest about eval size. "0.87 on 60 questions" is respectable and believable. "99% accurate" with no method makes experienced readers trust you *less*.

A client who reads "~$0.002 per answer, so 10,000 questions a month costs about $20 in API fees" can say yes to you without a meeting. That sentence is worth more than any adjective.

## 4. A one-page portfolio site

Your GitHub is for engineers. Many clients aren't engineers. A one-page site gives them a clean place to land, and it's the link you put in proposals, posts and your email signature.

One page, four sections:

1. **Hero**: your name, one line on what you build, and two buttons: "See my work" and "Book a call" (or your email).
2. **Projects**: three or four cards. Each card has a screenshot or GIF, a one-sentence outcome ("Answers HR questions from 40 policy PDFs, with citations"), one number, and links to the demo, video and code.
3. **Services**: what you'd build for a client, in plain words. "Chatbots that answer from your documents. Turning invoices and forms into spreadsheets. Automating repetitive email and data work."
4. **About and contact**: two sentences about you, where you are, your time zone, and how to reach you.

Keep it static: plain HTML and CSS, or a simple template, hosted on GitHub Pages, Netlify, Vercel or Cloudflare Pages. All of these have free tiers for a site like this. Buy a domain with your name if you can; it looks more serious than a subdomain, but it's optional.

What **not** to do: spend two weeks designing a portfolio site. A clean, fast, readable page in a weekend beats an animated one next month. The projects are the content.

## 5. Loom demos: the 2-minute walkthrough

A short screen-recorded walkthrough is the single most persuasive thing you can send a client, because it shows the product working **and** shows you communicating clearly. Loom is the common tool (free plan with time-limited videos at the time of writing; check current limits). Any screen recorder plus an unlisted YouTube upload works too.

A 2-minute structure that works:

| Time | What you show |
|---|---|
| 0:00–0:15 | The problem, in one sentence: "Teams waste hours searching policy PDFs." |
| 0:15–1:00 | The product doing one real task, start to finish. |
| 1:00–1:30 | One thing under the hood: the trace, the eval table or the cost per request. |
| 1:30–2:00 | Results and what you'd build for them: "I can set this up for your documents in about a week." |

Tips:

- Write bullet notes, not a script. Read-aloud scripts sound stiff.
- Do one or two takes, not twenty. Small stumbles make you sound human.
- Show your face in the corner bubble if you're comfortable; it builds trust quickly.
- Make one video per project, and later, short custom ones for specific clients (covered in the outreach lesson).

## 6. Before and after: weak versus strong descriptions

The same project, described twice.

**Weak:**

> An AI-powered chatbot built with cutting-edge LLM technology. Uses RAG and vector databases to provide intelligent answers. Built with Python, FastAPI, Docker, PostgreSQL.

Every sentence could describe ten thousand repos. "AI-powered", "cutting-edge" and "intelligent" are claims with no evidence. The tech list tells a client nothing about what they'd get.

**Strong:**

> Answers staff questions from 40 HR and policy PDFs, citing the page it used. 0.87 accuracy on a 60-question eval set; ~$0.002 per answer; median response 1.8 s. Hybrid search (vector + keyword) fixed misses on exact form names. Used by 12 people at a Lagos logistics company for 3 weeks.

Who it's for, what it does, how well, how cheap, one technical decision and real usage.

Another pair, for the extractor:

| Weak | Strong |
|---|---|
| "Document parser using LLMs and Pydantic." | "Turns supplier invoices into validated rows for a spreadsheet. 120 invoices in 2 minutes at $0.004 each; flags totals that don't add up for human review." |
| "Agent built with tool calling." | "Support-ticket agent that looks up orders and drafts replies. Resolves 71% of a 50-ticket eval set without a human; every run traced." |

The pattern for every description:

```
[What it does for whom] + [one number for quality] + [one number for cost or speed] + [one real-world signal]
```

> **Try it:** Rewrite the description of each of your four projects using that pattern. If you don't have a number for one of the slots, that tells you what to measure this week.

## Common mistakes

- **Leading with the tech stack.** Clients buy outcomes. Put the stack in the architecture section.
- **No demo.** If someone has to clone and configure your repo to see it work, most won't. GIF plus live link or video.
- **Dead links.** A broken demo is worse than no demo. Check every link before you send anything, and keep free-tier deployments awake or note that the first request may be slow.
- **Unverifiable numbers.** Say how each number was measured. If you can't explain it in one line, don't publish it.
- **Leaking secrets.** Check that `.env` is git-ignored and no API keys are in your commit history before you pin a repo.
- **Twenty half-done repos.** Four polished projects beat twenty starts. Pin the polished ones.
- **Waiting for perfect.** The roadmap says to start pitching in week 12, not after the portfolio is perfect. Good enough and live beats polished and private.

## Recap

- Make the evidence fast to see: profile README, four to six pinned repos, each with a one-line description.
- Every project README follows the formula: problem, demo GIF, architecture with reasons, results with numbers, how to run.
- Evals, cost per unit and latency are what make you look like an engineer rather than a demo-builder.
- A one-page site is for non-technical clients; a 2-minute Loom per project is your most persuasive asset.
- Describe each project as: what it does for whom, plus a quality number, a cost or speed number, and a real-world signal.
