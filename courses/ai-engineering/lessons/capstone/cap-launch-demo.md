# Launch, demo and case study

## Why this matters

A product nobody hears about doesn't get you gigs, and a repo with no explanation doesn't get you interviews. Week 11 turns a working capstone into proof: a product a stranger can start using without you in the room, a 2-minute video a client will actually watch, and a README that reads like a case study. These three things are what you'll send in every pitch and application in month 4. The engineering here is small (onboarding, empty states, rate limits); the communication is most of the work.

## 1. Onboarding: the first message does the selling

A new user decides in their first message whether your product is for them. Without you there to explain, the product must say what it does, what to try, and what it can't do.

For a WhatsApp or Telegram bot, send an onboarding message the first time you see a user, and again on "hi", "help" or "menu":

```python
ONBOARDING = (
    "Hi! I'm the assistant for Kemi's Fashion. I can answer questions about our products, "
    "prices, sizes and delivery, any time.\n\n"
    "Try: \"How much is the red ankara dress?\" or \"Do you deliver to Abuja?\"\n\n"
    "For orders and payments, I'll pass you to Kemi. Reply PRIVACY to see how we handle your messages."
)

GREETINGS = {"hi", "hello", "help", "menu", "start", "/start"}

def first_reply(is_new_user: bool, text: str) -> str | None:
    """Return the onboarding message when it's needed, else None (answer normally)."""
    if is_new_user or text.strip().lower() in GREETINGS:
        return ONBOARDING
    return None

print(first_reply(False, "Hello ") is not None)   # True
```

A good onboarding message has four parts: **who it is**, **what it can do**, **an example to copy**, and **its limits and how to reach a human**. The same applies to a web app: the empty state *is* the onboarding.

## 2. Empty states and polish

An **empty state** is what a screen shows before there's any content: no conversation yet, no CV uploaded, no meetings processed. Developers forget it because their test data fills every screen. Real users see it first.

- **Chat:** a one-line description and two or three example questions as clickable buttons.
- **Upload:** what files are accepted, the size limit, and a sample file to try without uploading their own.
- **History / dashboard:** "No meetings yet. Forward a transcript to notes@yourdomain.com to get started."

Then do a polish pass on the whole flow with fresh eyes (or, better, a friend who hasn't seen it):

- Every error message says what happened and what to do next.
- Nothing shows raw JSON, a stack trace, `None` or `undefined`.
- It works on a cheap Android phone on a slow connection.
- The page has a real title, and the bot has a proper name and profile picture.
- The README's live link works in a private browser window.

## 3. Rate limits and spend limits for the public

Once the link is public, you are paying for every stranger's curiosity. Three layers of protection, cheapest first:

1. **Input caps.** A maximum message length (Pydantic `Field(max_length=2000)`), a maximum file size, and a `max_tokens` on every call. These bound the cost of any *single* request.
2. **Per-user rate limits.** At most N requests per user per minute or hour. These bound the cost of any *single user*.
3. **A global spend cap.** A daily budget for the whole app; when it's reached, show "We've hit today's limit, back tomorrow" and alert yourself. This bounds your total bill. Also set a spend limit in the Claude Console so a bug can't run away with your money overnight.

A per-user limit as a FastAPI dependency, using the sliding-window `RateLimiter` you write in this lesson's exercise:

```python
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

from limits import RateLimiter   # your class from the exercise

app = FastAPI()
limiter = RateLimiter(limit=20, window=3600)   # 20 messages per user per hour

def rate_limited(x_user_id: Annotated[str, Header()]) -> str:
    if not limiter.allow(x_user_id):
        wait = int(limiter.retry_after(x_user_id)) + 1
        raise HTTPException(429, "You've sent a lot of messages. Please try again later.",
                            headers={"Retry-After": str(wait)})
    return x_user_id

@app.post("/chat")
def chat(user_id: Annotated[str, Depends(rate_limited)]):
    ...
```

Notes:

- **Key on something the user can't change easily.** On WhatsApp, the user id from the webhook. On a public web app without login, the client IP is the usual fallback (behind a proxy, read the `X-Forwarded-For` header your host sets, carefully), and it's imperfect: many Nigerian mobile users share IPs through carrier NAT. Pick generous limits.
- **In-memory limits reset on restart and aren't shared** between server processes. For one small server, that's fine. When you scale out, move the counters to Redis or your database.
- **On a messaging channel, don't return 429 to Meta.** The webhook should still return 200 (or it retries); instead, reply to the user once with "You've reached today's limit" and skip the LLM call.

## 4. The 2-minute demo video

Clients and hiring managers won't clone your repo. They will watch two minutes of video, if the first ten seconds give them a reason to. Record with Loom (free tier is enough) or any screen recorder, showing your screen and, ideally, your face in a corner.

A script that works, with rough timings:

| Time | What you show | What you say |
|---|---|---|
| 0:00–0:15 | The user's world: a screenshot of 40 unread WhatsApp chats | "Kemi runs a fashion shop in Lagos. She answers the same price and delivery questions 80 times a day, often at midnight." |
| 0:15–1:15 | The product doing the real job, end to end, with real-looking data | "Here's a customer asking about delivery to Ibadan… it answers in two seconds from Kemi's own price list. Here it doesn't know, so it hands over to Kemi." |
| 1:15–1:40 | One technical slide or the architecture diagram | "FastAPI backend, Claude Haiku with the catalogue in the prompt, webhook signature checks and idempotency, 48 eval cases in CI." |
| 1:40–2:00 | Results and a call to action | "Three weeks with three shops: 64% of questions answered without the owner, about $0.40 per shop per month in model costs. Link to the code and a live demo below." |

Tips:

- **Write the script and rehearse it twice.** Unscripted demos ramble to five minutes.
- **Lead with the problem, not the tech stack.** The stack is one slide near the end.
- **Show the failure path.** The "I don't know, I've asked Kemi" moment builds more trust than another perfect answer.
- **Use realistic data, never real customers' data.** Make up names and numbers, or get explicit permission.
- **Record in one go or cut ruthlessly.** Two minutes is a hard limit.

## 5. The case-study README

Your README is the written version of the demo, for readers who want depth. Structure it as a case study:

```markdown
# Kemi's Assistant: a WhatsApp support bot for small fashion shops

[2-minute demo video](https://www.loom.com/share/…) · [Live demo](https://…) · Built in 3 weeks, Nov 2026

## The problem
Small fashion shops in Lagos sell almost entirely on WhatsApp. The owner I worked with answered
~80 messages a day, most of them the same price, size and delivery questions…

## The solution
A WhatsApp bot that answers from the shop's own catalogue and FAQ, and hands everything
else to the owner. (Screenshot or GIF here.)

## Architecture
(Mermaid sequence diagram, component list, and links to the ADRs in docs/adr/.)
Why no RAG: the catalogue is ~4,500 tokens, so it goes in the prompt (ADR 001).

## Results
- 3 shops, 212 customer conversations over 2 weeks
- 64% of questions answered with no owner involvement (target: 60%)
- 0 wrong prices on a 48-case eval set, run in CI on every push
- ~$0.40 per shop per month in Claude costs (Haiku 5.5), median reply time 2.1 s

## What I learned
Customers send voice notes (~15% of messages); I added a polite "please type your question" reply…

## What I'd do next
Voice-note transcription, order capture into a Google Sheet, a WhatsApp template for "your order shipped".

## Running it
Setup, environment variables (.env.example), tests, deployment.
```

The **Results** section must contain real numbers from your logs and evals, and be honest about how they were measured. "64% (unrated answers counted as resolved; I spot-checked 50)" is more credible than a round number with no method. **What I'd do next** is where your cut features go: it shows you can prioritise.

## 6. Announcing it

Your marketing background is an advantage here: most engineers are bad at this part.

- **Post where your future clients are.** LinkedIn for businesses and recruiters; X for the developer community; local business and tech WhatsApp groups and communities.
- **Tell a story, not a feature list.** The problem, one person who had it, what you built, one real result, the demo video. Tag the business if they're happy to be named.
- **Make the call to action specific.** "If you run a business that answers the same WhatsApp questions all day, message me: I'm setting this up for two more shops this month." That's a pitch, and it's how month 4's gigs start.
- **Keep building in public.** Post the case study, then a short thread on one technical lesson (idempotent webhooks, or why you didn't need RAG). Each post sends people back to the demo.

Before you post, test every link from a phone, in a private window, logged out.

## Common mistakes

- **No onboarding.** New users type "hi", get a confused answer, and leave.
- **A public link with no rate limit or spend cap.** One shared link can cost you a month's budget in a night.
- **A demo that starts with the tech stack.** Start with the person and the problem.
- **A five-minute demo.** Nobody finishes it. Two minutes.
- **A README that's only setup instructions.** Add problem, solution, architecture, results, next steps.
- **Results with no numbers, or numbers with no method.** Measure, and say how.
- **Adding features during launch week.** Polish and explain what you have.

## Recap

- The first message (or empty state) says who it is, what it does, an example, and its limits.
- Polish the empty, error and mobile experience with someone who's never seen it.
- Protect the public launch with input caps, per-user rate limits (429 + `Retry-After` on web, a polite reply on WhatsApp) and a global spend cap.
- Record a scripted 2-minute demo: problem, product doing the job, one technical slide, results and a call to action.
- Write the README as a case study with honest, measured results and a "what I'd do next".
- Announce it with a story and a specific call to action, and keep building in public.
