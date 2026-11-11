# Choosing a problem worth three weeks

## Why this matters

You now have every core skill: you can call Claude, build a FastAPI backend, add retrieval, run an agent loop, write evals, ship a container and trace it in production. None of that is worth money until it's pointed at a problem someone actually has. Most failed side projects aren't bad code. They solve a problem nobody has, for a user nobody named. The next three weeks produce **one** product that real people use, and the choice you make this week decides whether that's possible.

The goal of this lesson is a one-page spec you'd be happy to show a business owner, and a scope you can finish.

## 1. What makes a good capstone problem

A good capstone problem has four properties:

1. **A specific person has it now.** Not "small businesses" but "Kemi, who runs a fashion shop in Yaba and answers 80 WhatsApp messages a day, most of them asking the price of something she posted on her Status".
2. **It happens often.** Daily or weekly pain gets used. A problem that comes up once a year won't produce three users in three weeks.
3. **They already spend time or money on it.** If they're paying an assistant, staying up late typing replies, or losing sales because replies are slow, there's value to capture. "It would be cool if…" is not a problem.
4. **LLMs are actually good at it.** Reading messy text, answering from documents, drafting, extracting fields, summarising, classifying. Not: exact arithmetic, real-time stock levels you can't access, or anything where one wrong answer is a disaster.

The fourth point is your edge. A business owner knows the pain; you know which parts of it a model can handle reliably and which need a human.

### Where to look

You have two rich hunting grounds, and your marketing background is an advantage in both.

**Local small businesses.** In Nigeria a huge share of small-business sales and customer service happens on WhatsApp: fashion and beauty shops, food vendors, phone and laptop sellers, pharmacies, tutors, event planners, logistics riders. The repeated work is obvious once you look: the same ten questions (price, sizes, delivery to my area, how to pay, are you open), order details copied by hand into a notebook or spreadsheet, and follow-ups that never get sent. Ask to sit with an owner for an hour and watch their phone.

**The job search.** You and everyone around you are in it. Tailoring a CV to each job post, writing cover letters, tracking which applications are where, preparing for interviews. Job seekers are easy to reach (your classmates, LinkedIn, campus groups), and you are a user yourself, which helps, as long as you test with people other than you.

Other good sources: your university (course reps drowning in repeated questions, student associations), churches and community groups (announcements, sign-ups), and any professional you know who complains about paperwork.

## 2. Talk to people before you build

The most common mistake is to build first and look for users after. Do it the other way round. Five conversations of twenty minutes each will tell you more than a week of coding.

The rule for these conversations: **ask about their past behaviour, not your idea.** People are polite. If you say "Would you use a bot that answers your customers?", most will say yes, and it means nothing. Ask instead:

- "Walk me through yesterday's messages. Which ones took the longest?"
- "What did you do the last time a customer asked about delivery to another state?"
- "How do you keep track of orders now? Can I see?"
- "Have you tried anything to fix this? What happened?"
- "If this took half the time, what would you do with the hours?"

Listen for **specifics** (numbers, names, screenshots, a notebook they show you), **workarounds** (copy-pasted reply templates, a cousin who helps on weekends), and **money or time already spent**. Those are signals of a real problem. Vague enthusiasm ("that sounds great!") isn't.

Write notes immediately after each conversation, in a plain text file:

```python
# A tiny habit that pays off: one dict per conversation, saved as JSON lines.
import json
from datetime import date

note = {
    "date": date.today().isoformat(),
    "who": "Fashion shop owner, Yaba (Instagram + WhatsApp)",
    "pain": "Same price/size/delivery questions all day; replies late at night",
    "evidence": "Showed 40 unread chats at 3pm; keeps a 'quick replies' note",
    "current_fix": "WhatsApp Business quick replies, sister helps on Saturdays",
    "would_pay": "Maybe ₦10k/month if it saves her evenings",
}
with open("interviews.jsonl", "a") as f:
    f.write(json.dumps(note) + "\n")
```

After five conversations, look for the pain that came up in three or more. That's your candidate.

> **Note:** You're not selling yet. If someone asks "how much?", say you're building it and would like them to try it free. Their willingness to try it, and to give you real data (a price list, a sample CV, a meeting recording), is the strongest validation you can get at this stage.

## 3. Validate before you write code

Before you commit three weeks, try to prove the idea wrong cheaply:

- **The Wizard-of-Oz test.** Do the job by hand for a day. Answer ten of Kemi's customer questions yourself, using her price list, in the tone she uses. If you can't answer them from the information she gives you, a model can't either. You'll also discover what information is missing (delivery fees by area, say).
- **The prompt test.** Paste the real material into a Claude chat (her price list and FAQ; a real CV and job post; a real meeting transcript) and try twenty real inputs. If quality is poor even with a careful prompt, the problem may need data you don't have.
- **The commitment test.** Ask: "If I have a first version next week, will you use it with real customers for a few days?" A yes with a date is a commitment. A "maybe, send it" is not.

If an idea fails these tests, good: you saved three weeks. Go back to your notes and pick the next one.

## 4. The one-page spec

When an idea survives, write it down on one page. It forces decisions you'd otherwise put off. Five parts:

| Part | Question it answers | Bad | Good |
|---|---|---|---|
| **User** | Who exactly? | "Businesses" | "Owners of 1–5 person fashion shops in Lagos who sell on WhatsApp" |
| **Job to be done** | What are they trying to get done? | "Use AI for customer service" | "Answer repeated price, size and delivery questions within a minute, any time of day" |
| **Success metric** | How will we know it works? (a number) | "Customers are happy" | "60% of incoming questions answered correctly without the owner, measured in week 2" |
| **Non-goals** | What are we deliberately not doing? | (empty) | "No payments. No Instagram DMs. No order tracking." |
| **Scope** | What ships in 3 weeks? | "Full platform" | "WhatsApp bot answering from the shop's price list and FAQ, with hand-off to the owner" |

**The job to be done** is phrased from the user's side. Nobody wants "an AI chatbot". They want to stop typing the same answer forty times a day.

**The success metric** must be a number you can measure with your logs. "60% of questions answered without the owner" can be counted. So can "a tailored CV in under 2 minutes, rated 4/5 or better by the user" or "action items from a 30-minute meeting with no missed owner or deadline in 8 of 10 test meetings". You'll come back to this number in *User testing and iteration*.

**Non-goals** are the most underrated part. Every user conversation produces feature requests. Non-goals are what you point at when you say "not in this version".

You can make your spec a little data structure and check it (this lesson's first exercise does exactly that):

```python
spec = {
    "user": "Owners of 1-5 person fashion shops in Lagos who sell on WhatsApp",
    "job_to_be_done": "Answer repeated price, size and delivery questions within a minute",
    "success_metric": "60% of questions answered correctly without the owner in week 2",
    "non_goals": ["payments", "Instagram DMs", "order tracking"],
    "weeks": 3,
}
missing = [k for k in ("user", "job_to_be_done", "success_metric") if not spec.get(k, "").strip()]
print(missing)  # []
```

## 5. Scoping to three weeks

Three weeks goes fast. Here's the shape from the section project:

- **Week 9:** spec, architecture, and a *walking skeleton*: the thinnest end-to-end path (message in → Claude → reply out) deployed to a real URL.
- **Week 10:** the core features, an eval set, and the first real users.
- **Week 11:** iterate from feedback, polish, launch, and write the case study.

To fit that, cut ruthlessly:

- **One user type.** Not "shop owners and their customers and delivery riders".
- **One channel.** WhatsApp *or* a web app, not both. (Telegram is fine for a first prototype; see *Messaging channels*.)
- **One core job.** The thing from your spec. Everything else is a non-goal.
- **Fake what you can.** An admin page can be a Streamlit app only you use. The business's price list can be a Google Sheet you export to CSV by hand. Login can wait if you have three known users.

A useful test: describe the product in one sentence that a user would say. "I send it the job post and my CV and it gives me a tailored CV and a cover letter." If you need "and also" twice, cut.

## 6. Three worked examples

These come from the roadmap. Each one is a realistic capstone; notice how each is scoped down.

### A. Job-application assistant

- **User:** final-year CS students and new grads in Nigeria applying to tech internships and junior roles.
- **Job:** turn one master CV into a version tailored to a specific job post, plus a short cover letter, without inventing experience.
- **Success metric:** 3 users each use it for 5+ real applications; 80% of tailored CVs rated "would send as is or with small edits".
- **Non-goals:** auto-applying to jobs, scraping job boards, interview coaching.
- **Pattern:** a workflow (extract requirements from the post → match to CV sections → rewrite → check nothing was invented), with structured output for the match step. A tracker of applications (a small SQLite table) is a stretch goal.
- **Main risk:** hallucinated experience. Your eval set must include "did it add a skill the CV doesn't have?"

### B. WhatsApp support bot for a local business

- **User:** one specific shop (start with one!) and its customers.
- **Job:** answer repeated questions from the shop's own price list, FAQ and delivery fees, and hand anything else to the owner.
- **Success metric:** 60% of incoming questions answered correctly with no owner involvement; zero wrong prices in a 50-question eval.
- **Non-goals:** payments, taking orders end-to-end, other channels.
- **Pattern:** RAG over a small document set (price list, FAQ) or simply the whole list in the prompt if it fits. Webhook-driven. A human hand-off path.
- **Main risk:** wrong prices, and the WhatsApp setup itself (business verification and Meta's rules take time). Prototype on Telegram or a web chat while you wait.

### C. Meeting notes → action items

- **User:** student project teams, church or club committees, or a small agency that meets weekly.
- **Job:** from a transcript or notes, produce a summary and a list of action items, each with an owner and a deadline, and send it to the group.
- **Success metric:** on 10 real meetings, every action item a human would list is captured, with the right owner, in 8 or more.
- **Non-goals:** recording and transcribing audio yourself (use exported transcripts from Google Meet, Zoom or a phone recorder app), calendar integration.
- **Pattern:** a single structured-output call (Pydantic model with `action_items: list[ActionItem]`), maybe a second "check" call. Email out.
- **Main risk:** messy transcripts and ambiguous owners ("someone should…"). Your eval needs real, messy examples.

All three are things businesses pay for, and they map directly onto freelance gigs: "AI chatbot for my business", "document extraction", "AI automation".

> **Try it:** Do the spec-checker exercise, then run it on the spec for your own idea. If it fails, fix the spec, not the checker.

## Common mistakes

- **Building for "everyone".** A product for everyone is tested by no one. Name one user type, ideally one real person.
- **Asking people if they like your idea.** They'll say yes. Ask about what they did last week.
- **Picking a problem LLMs are bad at.** Live inventory without access to the stock system, exact maths, legal or medical decisions with no human check.
- **No success metric, or one you can't count.** "Users like it" can't fail, so it can't guide you.
- **No non-goals.** Then every request becomes a feature and nothing ships.
- **Scoping to the vision, not to three weeks.** Ship the core job; the vision goes in "What I'd do next" in your README.
- **Waiting for perfect access.** WhatsApp approval, a company's data, or an API key from a partner can take weeks. Pick a problem you can start on today, and prototype on an easier channel.

## Recap

- A good problem: a specific person, frequent pain, time or money already spent, and a job LLMs are good at.
- Talk to five people about their past behaviour. Write notes. Look for pain that repeats.
- Validate cheaply: do it by hand, test real inputs in a chat, ask for a commitment with a date.
- Write a one-page spec: user, job to be done, a numeric success metric, non-goals, and a 3-week scope.
- Cut to one user type, one channel and one core job. Fake everything else.
