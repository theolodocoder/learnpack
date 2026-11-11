# Building in public

## Why this matters

Your first clients and your first interviewer will probably look you up before they reply. If they find a steady trail of posts showing what you built, what broke and what you learned, you're no longer a stranger with a CV: you're someone whose work they've already watched. Posting also brings inbound work. People message builders they've seen ship, and a single useful post can reach a founder who needs exactly your RAG setup. And you have an unfair advantage most engineers don't: a marketing background. You already know hooks, audiences and consistency. This lesson is about pointing those skills at your engineering work.

## 1. What "building in public" actually means

Building in public means sharing your work **while you do it**, not only when it's finished. It isn't self-promotion and it isn't motivational content. It's closer to a public lab notebook:

- what you're building and why,
- what you tried, what failed and what fixed it,
- numbers (accuracy, cost, latency) as they change,
- small tools and snippets other people can use.

The goal is that someone who scrolls your last ten posts concludes: *this person ships real LLM systems, measures them, and explains things clearly.* That's exactly the conclusion you want from a client or a hiring manager.

## 2. Where to post: X and LinkedIn

Post on both, with different emphasis.

| | X | LinkedIn |
|---|---|---|
| Audience | Builders, AI engineers, indie hackers, founders, researchers | Recruiters, hiring managers, business owners, non-technical clients |
| What works | Short build logs, demos, code screenshots, threads, replies to people in the field | Story-led posts, lessons learned, results framed as business outcomes |
| Tone | Casual, technical, fast | Clear, a little more structured, still personal |
| Why it matters for you | AI engineering community, startup founders hiring | Freelance clients in Nigeria and abroad, internship recruiters |

You can write one idea and adapt it twice. The X version leads with the technical detail; the LinkedIn version leads with the problem and the outcome.

**Target: 2 posts a week.** That's sustainable alongside study and client work. Consistency beats volume: two posts a week for six months beats twenty posts in one week and then silence.

## 3. What to post: five formats that work

### Build logs

What you did this week, with one concrete detail.

> Week 3 of building a chat-with-your-docs API.
>
> Vector search kept missing questions like "what's form HR-12?". Exact names don't embed well.
>
> Added keyword search alongside it and merged the results with reciprocal rank fusion. Hit rate on my 60-question eval went from 0.78 to 0.93.
>
> 40 lines of code. Biggest win so far.

### Lessons learned

One mistake and what it taught you. These are the posts people save and share, because they save the reader from the same mistake.

> I burned $14 in an afternoon testing my agent.
>
> The cause: every loop iteration resent the full conversation, including three 20-page documents.
>
> Fixes:
> 1. Summarise documents once, send the summary
> 2. Use Haiku for the tool-picking steps
> 3. Log tokens per call so you see this on day one, not day five
>
> Same task now costs about 4 cents.

### Demos

A 20–60 second screen recording of the thing working. Native video (uploaded directly, not a YouTube link) usually gets more reach on both platforms. Add one line of context and one number.

### Small tools

A script, a prompt template, a checklist or a tiny library that solves a narrow problem. "Here's the 30-line function I use to count tokens and cost for every Claude call" with a gist link. Useful things get bookmarked and reshared, and they show your code to people who'd never open your repos.

### Breakdowns

Explain one concept you recently understood, in your own words with your own example: "How hybrid search works, explained with my HR-policy bot." Teaching is the fastest way to show you understand something, and it's great prep for interviews.

## 4. Hooks: the first line decides everything

On both platforms, people see a line or two before deciding whether to expand the post. That first line is the hook. You know this from marketing: the headline does most of the work.

Hook patterns that fit honest engineering content:

| Pattern | Example |
|---|---|
| Specific result | "My RAG bot's accuracy went from 0.74 to 0.87 with one change." |
| Surprising cost or number | "I burned $14 in an afternoon testing my agent." |
| Mistake | "My chatbot confidently quoted a policy that doesn't exist. Here's why." |
| Before/after | "Before: 6 hours a week copying invoice data. After: 4 minutes." |
| Useful promise | "The 5 evals I run before shipping any LLM feature:" |
| Contrarian (only if true) | "You probably don't need a vector database for your first RAG app." |

Rules for good hooks:

- **Specific beats clever.** Numbers, names and concrete nouns.
- **The post must deliver what the hook promises.** A hook that oversells loses trust.
- **No clickbait about AI replacing everyone.** You want clients and engineers to respect you, not to argue with you.

Since you think in data, you can treat hooks like any experiment. Keep a small log and look at what works after a month:

```python
import csv
from io import StringIO
from statistics import mean

log = StringIO("""date,platform,format,hook,impressions,replies
2026-11-03,x,build-log,"Hit rate 0.78 -> 0.93 with one change",4100,9
2026-11-05,linkedin,lesson,"I burned $14 testing my agent",7300,22
2026-11-10,x,demo,"Chat with 40 policy PDFs, cited answers",2600,4
2026-11-12,linkedin,build-log,"Week 4 of my RAG API",900,1
""")

by_format: dict[str, list[int]] = {}
for row in csv.DictReader(log):
    by_format.setdefault(row["format"], []).append(int(row["replies"]))

for fmt, replies in sorted(by_format.items(), key=lambda kv: -mean(kv[1])):
    print(f"{fmt:10} avg replies {mean(replies):.1f} over {len(replies)} posts")
# lesson     avg replies 22.0 over 1 posts
# build-log  avg replies 5.0 over 2 posts
# demo       avg replies 4.0 over 1 posts
```

Track **replies and DMs**, not just impressions. A post seen by 900 people that gets one message from a business owner is worth more than a viral one that gets none.

## 5. Turning one project into five posts

Every project you've built is a month of content. Take your document extractor:

1. **The problem post.** "Accountants I spoke to spend hours retyping invoice data. I'm building a tool that turns invoices into clean spreadsheet rows. Here's the plan." (Post this *before* or *while* you build.)
2. **The technical-decision post.** "Why I used Pydantic models with `messages.parse` instead of asking the model for 'JSON please'." Include a short code screenshot.
3. **The failure post.** "My extractor said an invoice totalled ₦4,500,000. It was ₦45,000.00. The fix: a business-rule check that line items add up to the total, and a 'needs review' flag."
4. **The numbers post.** "120 invoices in 2 minutes, $0.004 each. Here's how I measured cost per document." Show the cost report.
5. **The demo post.** A 45-second video of a folder of invoices becoming a spreadsheet. End with: "If your team does this by hand, I can set it up for you. DMs open."

Notice the last line. One post in five can be a soft offer. The other four earn the right to make it.

> **Try it:** Pick your capstone and draft the five post ideas (one line each) for problem, decision, failure, numbers and demo. Schedule them for the next two and a half weeks at two per week.

## 6. Using your marketing edge

Most engineers post rarely, bury the point and never think about the audience. You can do better with skills you already have:

- **Know the audience for each post.** "Is this for engineers or for business owners?" changes every word. Engineers want the how; owners want the outcome and the cost.
- **Benefits over features.** You'd never sell a product by listing its ingredients. Don't sell a RAG system by listing pgvector and FastAPI.
- **Positioning.** Pick a lane that people can remember: "the person who builds document-AI for Nigerian SMEs" or "RAG and evals". A narrow lane is easier to refer people to.
- **Consistency and a calendar.** Batch-write posts on a weekend and schedule them.
- **Repurposing.** One LinkedIn post becomes an X thread, a section of your portfolio site and a talking point in a discovery call.
- **Writing clear copy.** Short sentences, one idea per post, white space. You've done this professionally.

There's a real gap here: plenty of good AI engineers can't explain their work to a client, and plenty of marketers can't build. You can do both, and building in public is where people see that.

## 7. Engaging with the AI engineering community

Posting into a void is slow. Replies grow your network faster than posts.

- **Reply thoughtfully** to engineers, founders and researchers you respect. Add a fact, a result or a question, not "Great post!". "I saw the same thing: hybrid search raised my hit rate from 0.78 to 0.93 on legal docs" starts a conversation.
- **Share other people's work** with your own take: "Tried this chunking approach on my HR bot; here's what happened."
- **Answer beginner questions.** You were a beginner three months ago; you remember what was confusing.
- **Join communities** where builders hang out: local tech communities in Nigeria, AI engineering Discord and Slack groups, and the GitHub discussions of tools you use. Contributing a small fix or doc improvement to an open-source tool you rely on is also a strong signal.
- **DM sparingly and specifically.** "I liked your post on agent evals; I built something similar for support tickets and found X. Would love your take on Y." Short, specific and easy to answer.

## 8. Honest, not hype

The AI space is full of exaggeration: "I built a $10k/month SaaS in a weekend with no code", "This prompt replaces your whole team". It's tempting to copy that style because it gets reach. Don't. Your audience includes the people who'll hire you, and they've seen through it a hundred times.

Honest posting looks like:

- **Real numbers with context.** "0.87 on a 60-question eval set", not "near-perfect accuracy".
- **Saying what doesn't work.** "It still fails on scanned PDFs." This makes everything else you say more believable.
- **Calibrated language.** "In my tests", "for this kind of document", "so far".
- **Credit.** Name the docs, tutorials and people you learned from.
- **No fake screenshots or inflated revenue.** If you're asked about a claim in an interview, you want to be able to show the receipts.

Honesty also protects you. If a client hires you because of a post, the post becomes part of their expectations. Overclaiming online turns into a hard conversation on a project later.

## Common mistakes

- **Only posting when something is finished.** The process is the content. Post during the build.
- **Writing for engineers when you want clients** (or the reverse). Decide who each post is for.
- **Posting links with no context.** Say what it is, why it matters and one number, in the post itself.
- **Selling in every post.** At most one soft offer for every four or five useful posts.
- **Chasing reach over relevance.** Viral posts about AI drama don't bring clients. Specific, useful posts do.
- **Quitting after three weeks.** Growth from posting is slow at first. Commit to 12 weeks of two posts a week before judging it.
- **Sharing client details without permission.** Ask before naming a client or showing their data. Anonymise by default.

## Recap

- Building in public is a public lab notebook: builds, failures, numbers, small tools.
- Post twice a week on X (builders) and LinkedIn (clients and recruiters), adapting each idea for the audience.
- Hooks decide whether a post is read; make them specific and make the post deliver.
- Every project is five posts: problem, decision, failure, numbers, demo with a soft offer.
- Your marketing background is a real advantage: audience, benefits, positioning, consistency.
- Engage through thoughtful replies, and stay honest: calibrated claims build the trust that gets you hired.
