# Freelance gigs: finding, winning and delivering

## Why this matters

Freelance work is the fastest route from "I've built things" to "I've been paid to build things". It gives you income, real client problems, testimonials and a track record, which is exactly what you need for full-time roles later. The four projects you've built map almost one-to-one onto the AI gigs posted every day. This lesson covers where those gigs are, how to win them, how to price and scope them so you don't get burned, and how to get paid from Nigeria.

> **Note:** Platform fees, payout options and payment-provider availability change often and differ by country. Wherever this lesson mentions them, check the current details on the official site before you rely on them.

## 1. Where the gigs are

| Channel | Good for | Watch out for |
|---|---|---|
| **Upwork** | Highest volume of AI and automation jobs; clients used to hiring remote freelancers | Very competitive; proposals cost "Connects" (platform credits); new profiles need a first win to build momentum |
| **Contra** | Portfolio-first profiles, project-based work, a design- and startup-friendly audience | Smaller volume than Upwork; check its current fee model on its pricing page |
| **LinkedIn** | Posts and DMs from founders and managers; "looking for someone who can build…" posts; your network | No escrow or payment protection; you handle contracts yourself |
| **Direct outreach** | Local and international small businesses with an obvious problem you can solve | Takes effort per prospect; covered fully in the outreach lesson |
| **Referrals** | The best-paying, easiest-to-close work; comes from past clients, classmates, lecturers and your followers | Slow to start; you need a few happy clients first |

Start with **two** channels, not five: Upwork (or Contra) for volume, plus direct outreach and LinkedIn for higher-value work. Referrals grow on their own once you deliver well.

### Searching for gigs on Upwork and Contra

Use the vocabulary clients use, not the vocabulary engineers use. Save these searches and check them daily:

- "RAG", "chat with documents", "AI chatbot", "custom GPT", "knowledge base chatbot"
- "document extraction", "invoice OCR", "PDF to Excel", "data extraction AI"
- "AI automation", "workflow automation", "Zapier AI", "n8n", "Make.com"
- "LLM integration", "OpenAI API", "Claude API", "AI feature"
- "AI agent", "AI assistant"

**Apply early.** Jobs posted in the last few hours get read; jobs with 50+ proposals usually don't. Turn on alerts for your saved searches.

**Filter clients.** Prefer clients with a verified payment method, some hiring history and reasonable reviews of past freelancers. A brand-new client with no history isn't always bad, but scope those jobs more carefully.

## 2. Gig types that match what you've built

| Gig as clients describe it | Your matching project | What you'd deliver |
|---|---|---|
| "Chatbot that answers questions from our docs / website / knowledge base" | Chat-with-your-docs RAG API | Ingestion of their documents, a hosted API or widget, citations, a small eval set |
| "Extract data from PDFs / invoices / CVs into Excel or our database" | Document extractor | A script or service: files in, validated rows out, with a review queue for failures |
| "Automate our email / lead / support workflow with AI" | Agent with evals | A workflow that classifies, drafts or routes, with tool calls into their systems and logging |
| "Add AI to our app" (summaries, search, classification) | All of them | An API endpoint, prompts with tests, cost estimates |
| "Fix / improve our existing chatbot" | RAG + evals | An eval set to measure it, then targeted fixes (chunking, hybrid search, prompts) |

That last row is underrated. Many businesses already built a chatbot that works "most of the time". Offering to **measure** it with an eval set and then fix the worst failures is a clear, scoped, valuable job that few freelancers pitch.

## 3. Writing proposals that win

Most proposals are about the freelancer: "Hello, I am an experienced AI developer with expertise in Python, LangChain, OpenAI…". Clients skim past these. A winning proposal is about **their problem**.

The structure:

1. **Their problem, in your words** (1–2 sentences). Show you read the post.
2. **A relevant demo** (1 sentence + link). The closest thing you've built, ideally a 2-minute Loom.
3. **Your approach** (3–4 bullets). Concrete enough to show you know how; not a full spec.
4. **A fixed scope with a price and timeline**, or a clear next step.
5. **One question** that shows thinking and invites a reply.

Example, for a job "Need an AI chatbot that answers customer questions from our product manuals (about 30 PDFs)":

```
Hi Sarah, you want customers to get answers from your 30 product manuals without
waiting for support, and the answers need to be right, since a wrong spec could
mean a wrong order.

I built almost exactly this: a chatbot that answers from 40 policy PDFs and cites
the page it used. 2-minute demo: https://loom.com/share/...

How I'd do it for you:
- Load and split your manuals, keeping page numbers so every answer cites its source
- Hybrid search (meaning + exact model numbers), which matters for product codes
- A 40-question test set from your real support emails, so we measure accuracy before launch
- Hosted API + a simple chat widget for your site

Fixed scope: working chatbot on your manuals, test-set report, and the widget,
in 10 days for $X. Hosting and API costs are separate and small; I'll estimate them for you.

Quick question: do customers usually ask by product name or by model number?
That changes how I set up search.

Ada
```

Why it works: it opens with her problem, proves you've done it, shows you understand a risk she cares about (wrong specs), commits to a scope, and asks a question she'll want to answer.

> **Try it:** Find one real "AI chatbot" or "data extraction" job post today. Write a proposal using the five-part structure in under 150 words, without sending it. Then compare it with the generic proposal you'd have written a month ago.

### Small things that matter

- **Keep it short.** 100–200 words. Clients read dozens.
- **Answer every question in the post.** Some clients add "start your reply with the word 'banana'" to filter out copy-paste proposals.
- **Don't paste the same proposal everywhere.** Personalise the first two lines at least.
- **Never use AI-generated proposals unedited.** Clients recognise them instantly. Use a template, then write the specific parts yourself.

## 4. Pricing

### Fixed-price packages versus hourly

| | Fixed price | Hourly |
|---|---|---|
| Client's view | Knows the total up front; easy to approve | Open-ended; harder to approve |
| Your view | You earn more as you get faster; risk if scope grows | Safe when scope is unclear; you're paid for every hour |
| Best for | Well-defined builds: "chatbot on 30 PDFs", "invoice extractor" | Ongoing work, debugging unknown systems, maintenance |

For your first gigs, **fixed-price packages** are usually easier to sell. A package is a named, scoped offer:

```
Starter: Docs chatbot
- Up to 50 documents (PDF/DOCX)
- Hosted API + chat widget
- 30-question accuracy report
- 1 round of revisions, 14 days of bug fixes
- Delivered in 10 working days
```

Packages make pricing a choice between your options rather than a negotiation about your hourly rate. Many freelancers show two or three tiers (a basic, a standard and a more complete version).

### How to set the number

There's no correct rate, and this lesson won't give you one: rates vary a lot by client, country and platform, and change over time. A practical approach:

1. **Look at the market.** On Upwork, open completed jobs similar to yours and see what clients paid. Look at what freelancers with similar portfolios charge.
2. **Estimate your hours honestly**, then add a buffer (things always take longer: client data is messier than demos).
3. **Price on value, not just hours.** If the extractor saves an accountant 6 hours a week, a price that pays back in a month or two is easy to justify.
4. **Start a bit lower to win your first 2–3 reviews, then raise prices** with each new client. Don't stay cheap for long; low prices attract the most demanding clients.

### Anchoring with a discovery call

For anything bigger than a small fixed gig, get on a short call before quoting. On the call you learn the real problem, the client's budget range and what success looks like. Then you can **anchor**: present a fuller package first ("the complete version with an admin panel and monthly accuracy reports is $Y"), then the leaner option. The first number heard shapes what feels reasonable. Use this honestly: every option you present must be one you'd genuinely deliver.

### Running costs

LLM projects have ongoing costs (API tokens, hosting, a vector database). Always state them separately and estimate them from your cost-per-unit numbers: "about $15–25/month in API costs at your volume". Recommend the client puts API keys and hosting on **their own accounts and cards**, so you're never paying their usage.

## 5. Scoping and change requests

Most freelance pain comes from unclear scope. Write the scope down before starting, even for small jobs:

- **Deliverables:** exactly what you'll hand over (a repo, a deployed URL, a report).
- **Inputs:** what the client provides and by when (documents, access, sample data).
- **Out of scope:** what's not included (mobile app, handling scanned images, a user login system).
- **Acceptance:** how you both know it's done (e.g. "≥ 0.8 on the agreed 30-question test set").
- **Revisions and support:** number of revision rounds and how long you'll fix bugs for free.

When the client asks for more ("can it also answer from our WhatsApp chats?"), don't say yes on the spot and don't say no. Say:

```
Good idea. That's outside the current scope, so I'll treat it as a change request.
It's about 3 extra days of work for $Z. Want me to add it now, or after we launch
the current version?
```

That keeps the relationship friendly and stops a fixed-price job turning into unpaid work. Small, quick requests you can do as goodwill, but say so: "This one's on me."

## 6. Contracts and getting paid

### On platforms

Upwork and Contra provide contracts and payment flows. On Upwork, fixed-price work is split into **milestones** that the client funds before you start each one; hourly contracts are tracked through Upwork's desktop app. **Keep all work and payment on the platform** for platform clients: taking payment off-platform usually breaks the terms of service and removes your protection.

### Off-platform clients

For direct and LinkedIn clients, use a simple written agreement (a one- or two-page statement of work is enough) covering scope, price, payment schedule, timeline, who owns the code (usually the client, once paid in full) and confidentiality. Then:

- **Ask for a deposit** before starting (commonly part of the fee up front, the rest on delivery or by milestone).
- **Send proper invoices** with your name, the client's name, the work, the amount, currency and payment details.
- **Deliver against milestones**, so neither side carries too much risk.

### Receiving international payments from Nigeria

Options Nigerian freelancers commonly use include:

- **The platform's own payout options.** Upwork and Contra each list withdrawal methods by country (such as bank transfer or a payment provider). Check what's available for Nigeria in your account settings.
- **Payoneer**: widely used to receive from marketplaces and international clients, with receiving accounts in several currencies.
- **Grey**: offers foreign-currency receiving accounts aimed at Africans working with international clients.
- **Wise**: popular internationally, but the features available depend on where you live; check what Wise currently supports for residents of Nigeria before relying on it.
- **A domiciliary (foreign-currency) account** at a Nigerian bank, for receiving international transfers directly.

> **Note:** Fees, exchange-rate margins, withdrawal limits and availability for Nigerian users change, sometimes with new regulations. Before choosing, read each provider's current pricing page, check recent experiences from other Nigerian freelancers, and test with a small payment first. Keep records of every payment for tax purposes.

Practical habits:

- Set up and verify at least **two** payout methods before your first client pays you. Verification can take days.
- Invoice in USD (or the client's currency) for international clients, and be clear about who pays transfer fees.
- Keep a simple spreadsheet of invoices: client, amount, currency, date sent, date paid.

## 7. Delivering and getting testimonials

Delivery is where you earn the next job.

1. **Communicate more than you think you need to.** A short update every 2–3 days: what's done, what's next, any blockers. Silence is what makes clients nervous.
2. **Demo before you deliver.** A short Loom walking through the finished work, how to use it and the test results.
3. **Hand over properly.** README, a short "how to run and update this" guide, credentials transferred to the client's accounts, and the eval report.
4. **Fix the bugs you promised to fix**, quickly, during the support window.
5. **Ask for a review and a testimonial** when the client is happiest, right after a successful handover:

```
Really glad the chatbot's working well for your team. If you're happy with how it went,
would you mind leaving a short review? And could I quote a sentence or two from you
on my site, with your name and company? Something like what the bot changed for your
support team would be ideal.
```

Then ask: "Is there anything else in your business that's eating up time like this did?" That question turns one-off gigs into the next project.

## Common mistakes

- **Applying to everything.** Ten carefully chosen, personalised proposals beat fifty generic ones.
- **Pricing on fear.** Extremely low prices attract difficult clients and train you to undervalue your work.
- **Starting without written scope.** Even a bullet list in a message is better than nothing.
- **Absorbing every change request.** Use the change-request script; scope creep kills fixed-price projects.
- **Paying for the client's API usage.** Put keys and billing on the client's accounts.
- **Leaving the platform to "save fees".** You lose protection and risk your account.
- **Overpromising accuracy.** Promise a measured target on an agreed test set, not "100% accurate".
- **Going quiet during a project.** Regular short updates prevent most disputes.

## Recap

- Gigs come from Upwork and Contra (volume), LinkedIn and direct outreach (higher value), and referrals (best of all).
- Your four projects map to the most common AI gigs: docs chatbots, document extraction, automation and LLM integration.
- Winning proposals lead with the client's problem, link a relevant demo, commit to a fixed scope and ask one smart question.
- Prefer fixed-price packages early; anchor with a discovery call; state running costs separately.
- Write scope down, treat additions as change requests, and get paid through the platform or with deposits and invoices.
- From Nigeria, compare platform payouts, Payoneer, Grey, Wise and domiciliary accounts, and check current fees and availability yourself.
- Deliver with regular updates and a demo, then ask for a review, a testimonial and the next problem.
