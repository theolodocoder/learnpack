# Real users, feedback and iteration

## Why this matters

"Used by at least 3 real people" is the line between a demo and a product, and it's what makes your capstone credible to a client or an employer. Real users do things you'd never test: they send voice notes, type in Pidgin, ask two questions in one message, paste a whole PDF. Watching them is the fastest way to find what's broken. Turning what they hit into eval cases is how you make sure it stays fixed. This lesson is about running that loop for two weeks without drowning in feature requests or mishandling people's data.

## 1. Getting your first three users

Three is a small number, but each one has to use the product for real, more than once. Where they come from:

- **The people you interviewed.** They told you about the problem; now ask them to try the fix. This is why you took notes and asked for a commitment in *Choosing a problem worth three weeks*.
- **Your own network.** Classmates for the job assistant; a relative's shop or a friend's food business for the support bot; your student association or church committee for meeting notes.
- **One business counts for more than one user.** If Kemi's shop uses your bot, Kemi is one user and her customers are more. Count the people who actually interacted.

Make the ask concrete: "Can you use it for your next five applications this week, and spend 20 minutes with me on Friday?" A specific task and a specific time get a yes far more often than "try it and tell me what you think".

## 2. Watch them use it

Your most valuable hour of the week is sitting next to a user (or on a video call with screen sharing) while they use the product for a real task. The rules:

- **Give a task, not a tour.** "Here's a job post you're actually interested in. Get a CV ready for it." Then stop talking.
- **Don't help.** When they hesitate, count to ten. Where they get stuck is your data. If you explain, you lose it.
- **Ask them to think aloud.** "Just say what you're looking for as you go."
- **Write down what they do, not what they say.** "Scrolled up looking for the upload button for 40 seconds" beats "said it was easy".
- **Ask about the past at the end.** "How did you do this last time? Was this faster?" Not "would you use this?"

Afterwards, write three lists: **broke** (errors, wrong answers), **confused** (they didn't know what to do), **wanted** (feature requests). Most of week 10's work comes from the first two lists. The third mostly goes in your non-goals or your "what I'd do next".

## 3. Collect feedback in the product

You can't watch every session. Build feedback into the product so it reaches you every day:

- **Thumbs up / down** on every answer, stored against the message id (the `feedback` table from *From spec to architecture*). In WhatsApp, interactive reply buttons work, or simply "Reply 1 if this helped, 2 if not".
- **A correction box** after a thumbs-down, or for the business owner on an admin page: "What should it have said?" That correction is gold: it's a labelled test case written by an expert.
- **A short check-in** at the end of each week: three questions, by message, not a long survey.

## 4. Logging conversations: consent and privacy

To improve the product you need to read what users sent and what the model replied. That means storing personal data, so do it properly from day one.

**Ask for consent and say what you do.** Before logging anyone, tell them, briefly and in plain words, and give them a way to say no. For a WhatsApp bot, the first reply can include it. For a web app, a line under the input box. Here's a privacy note you can adapt:

```text
Privacy: To improve this assistant, we store your messages and its replies for up to 90 days.
We remove phone numbers and email addresses before saving. Your messages are processed by
Anthropic's Claude to generate replies. We never sell your data or use it for marketing.
To see or delete your data, message "DELETE MY DATA" or email privacy@yourdomain.com.
```

That note is short, but it covers what's collected, why, how long it's kept, who processes it, and how to get it deleted. Then actually honour it: write the delete function and the retention clean-up job, even if they're ten lines each.

> **Note:** Nigeria's **Nigeria Data Protection Act 2023**, enforced by the Nigeria Data Protection Commission (NDPC), requires a lawful basis (such as consent) for processing personal data, transparency about it, and protection of it. Other countries have similar laws (the GDPR in Europe). A capstone isn't a legal review, but collecting only what you need, telling people, getting consent and letting them delete their data covers the basics. A business that pays you will ask about this.

**Minimise and redact.** Don't store what you don't need. Before writing a message to your logs:

- **Redact personal identifiers** in the text: phone numbers, emails, and anything else sensitive in your domain (account numbers, addresses).
- **Pseudonymise the user id.** Store a salted hash instead of the phone number, so you can still group one user's messages without knowing who they are. Keep the salt in an environment variable, not in the database.

```python
import hashlib
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

def pseudonym(user_id: str, salt: str) -> str:
    return hashlib.sha256((salt + user_id).encode()).hexdigest()[:12]

print(EMAIL.sub("[EMAIL]", "send it to ada.obi@gmail.com please"))   # send it to [EMAIL] please
print(pseudonym("2348031234567", "s3cret") == pseudonym("2348031234567", "s3cret"))  # True
```

The exercise extends this to Nigerian phone numbers in all their common formats: `08031234567`, `0803 123 4567`, `+234 803 123 4567`, `2348031234567`. Regex redaction catches formatted identifiers; it won't catch "I live at 12 Allen Avenue". For a capstone, that's an acceptable, documented limit.

**Separate what the product needs from what you analyse.** The bot may need the real phone number to reply (in the users table, access-controlled). Your analysis logs and eval sets don't: they get the redacted, pseudonymised version.

## 5. From feedback to eval cases

You built eval suites in the agents and evals lessons. User feedback is where the best cases come from, because they're the questions real people actually ask, in their actual words.

A pipeline you can run every few days:

1. **Thumbs-down with a correction** → an eval case: input = the user's question, expected = the correction. This is a bug you've seen; the case makes sure it stays fixed.
2. **Thumbs-up** → a regression case: the answer was good, keep it good when you change the prompt or model.
3. **Thumbs-down without a correction** → a review queue. Someone (you, or the business owner) writes the correct answer, then it becomes case 1.
4. **Deduplicate** near-identical questions so one popular question doesn't dominate your score.

```python
logs = [
    {"id": 1, "question": "Do you deliver to Ibadan?", "answer": "No.", "rating": "down",
     "correction": "Yes, in 2 days for ₦3,500."},
    {"id": 2, "question": "Opening hours?", "answer": "9am-6pm, Mon-Sat.", "rating": "up"},
]
cases = [{"input": l["question"], "expected": l.get("correction") or l["answer"]}
         for l in logs if l["rating"] == "up" or l.get("correction")]
print(len(cases), cases[0]["expected"])   # 2 Yes, in 2 days for ₦3,500.
```

How you *grade* each case depends on the product: an exact check for facts that must be right (a price must contain "₦3,500"), and an LLM judge with a rubric for open-ended answers (is this tailored CV faithful and relevant?). Keep the cases in a JSON file in the repo, and run them in CI so every prompt change is checked against everything real users taught you.

> **Try it:** The feedback-to-evals exercise builds steps 1–4. Run it on a week of your own logs.

## 6. Measuring the success metric

Your spec has a number in it. Measure it from the logs, weekly, the same way each time. For the shop bot's "60% of questions answered correctly without the owner":

```python
week = [
    {"handed_off": False, "rating": "up"},
    {"handed_off": False, "rating": None},
    {"handed_off": True,  "rating": None},
    {"handed_off": False, "rating": "down"},
    {"handed_off": False, "rating": "up"},
]
resolved = sum(1 for m in week if not m["handed_off"] and m["rating"] != "down")
print(f"{resolved / len(week):.0%}")   # 60%
```

Be honest about what the number means. Here, an unrated answer counts as resolved, which is optimistic; say so in your write-up, and spot-check a sample by hand. Track a few supporting numbers alongside it: messages per user per week (are they coming back?), cost per conversation (from your token counts), and response time.

## 7. Weekly iteration, and knowing when to stop

Run week 10 and week 11 as short cycles:

- **Monday:** read the logs and feedback; update the three lists (broke, confused, wanted); add new eval cases.
- **Tuesday to Thursday:** fix the top items from "broke" and "confused". Run the evals after every prompt or model change; a fix that breaks three old cases isn't a fix.
- **Friday:** ship, tell your users what changed ("You asked for X, it's live"), and measure the success metric.

**Prioritise by frequency × severity.** A wrong price that happens once a day beats a missing feature someone mentioned once. Wrong answers come before missing features, always.

**Know when to stop adding features.** Stop when:

- the core job meets the success metric for your three users;
- the requests you're getting are for *different* jobs (that's a new product, or "what I'd do next");
- you're in week 11. Week 11 is for polish, the launch and the case study, not new features.

Every feature you add in the last week is untested by real users and is one more thing that can break during your demo. Write it down in the README instead. "Users asked for order tracking; here's how I'd add it" shows judgment, which is exactly what clients and interviewers are looking for.

## Common mistakes

- **Testing only with yourself.** You know how it's meant to work. Your users don't.
- **Helping during a usability session.** Watch where they get stuck; that's the point.
- **Logging everything with no consent or redaction.** It's a legal and trust risk, and it's easy to avoid.
- **Collecting feedback you never read.** Schedule the Monday review.
- **Fixing bugs without adding eval cases.** The same bug comes back next prompt change.
- **Chasing every feature request.** Check it against your spec and non-goals first.
- **Changing the success metric to fit the result.** Report the real number and what you learned.

## Recap

- Get three real users with a concrete ask: a specific task and a specific time.
- Watch them do a real task without helping; record what broke, what confused them, what they wanted.
- Build thumbs up/down and corrections into the product.
- Get consent with a short privacy note; redact phone numbers and emails and pseudonymise user ids before logging; honour deletion.
- Turn corrections and good answers into eval cases, deduplicated, run in CI.
- Measure your success metric weekly; fix wrong answers before adding features; stop adding features in week 11.
