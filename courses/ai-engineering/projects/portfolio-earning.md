# Project: Launch your AI engineering career

This project is different from the others. There's no new code to ship. Instead, you'll turn the four systems you've already built into **paid work and interviews** over the next 30 days, following a written plan with weekly targets and tracking your results like an experiment.

When you're done, paste your **GitHub profile URL** into the repo field and your **portfolio site URL** into the live-URL field below.

> **Note:** You don't need to finish your portfolio before you start pitching. The plan overlaps them on purpose: replies take time to arrive, so the earlier your first pitches go out, the sooner you'll hear back.

## What "done" looks like after 30 days

- A GitHub profile and one-page site that make your work obvious in 30 seconds.
- A Loom demo for each project.
- A marketplace profile (Upwork and/or Contra), payout methods set up, a proposal template and a fixed-price package.
- 40+ personalised pitches, 8+ posts and 20+ role applications sent, all tracked.
- A written review of what worked, with next month's targets.

Success isn't "a client signed in 30 days", because that depends partly on luck and timing. Success is doing the work consistently, measuring it, and improving the parts that aren't working. If you do that, clients and interviews follow.

## Targets

| Activity | Weekly target | 30-day total |
|---|---|---|
| Personalised pitches (marketplace proposals + direct outreach) | 10 | 40+ |
| Follow-ups on unanswered pitches | as due | all of them |
| Build-in-public posts (X and LinkedIn) | 2 | 8+ |
| Thoughtful replies in the AI engineering community | 10 | 40+ |
| Internship / junior applications (tailored) | 5–7 | 20+ |
| Live-coding practice (practical Python) | 3 sessions | 12 |
| System-design practice out loud | 1 | 4 |

Adjust the numbers to your university timetable, but write the adjusted numbers down at the start and stick to them.

## The 30-day plan

### Week 1: portfolio, foundations, first pitches

- **Profile README**: positioning line, your 3–4 projects each described as *what it does for whom + quality number + cost/speed number + real-world signal*, links and a clear ask.
- **Pinned repos**: pin your best 4–6; give each a description and topics. Rewrite the README of your **strongest** project using the formula: problem, demo GIF, architecture with reasons, results table, how to run, limitations.
- **Loom**: record the 2-minute demo for that project.
- **Marketplace profile**: create or finish your Upwork and/or Contra profile. Title in client language ("AI engineer: RAG chatbots, document extraction, LLM automation"), an overview that leads with outcomes, and portfolio items using your GIFs and Looms. Save the gig searches from the freelance lesson and turn on alerts.
- **Payouts**: set up and start verifying two payout methods. Check the current fees and availability for Nigeria on each provider's own site.
- **Tracker**: create it (see below).
- **Pitches**: send your first **10**: around 6 marketplace proposals and 4 direct outreach messages.
- **Posts**: 2. A good first one: "Here's what I built in the last 3 months", with one number per project.

### Week 2: finish the portfolio, open the second front

- Rewrite the other project READMEs with the same formula; record the remaining Looms.
- **Portfolio site**: one page (hero, projects, services, contact), deployed on a free static host. Link it from GitHub, LinkedIn, X and your marketplace profile.
- **Packages and templates**: write one fixed-price package for your strongest gig type (scope, deliverables, out of scope, timeline, revisions, price, running costs) and a proposal template following the five-part structure.
- **Resume**: one page, projects first, every bullet an action + technical choice + number.
- **Niche**: choose one niche for direct outreach and build a list of 30 qualified prospects, each with a visible problem noted.
- **Pitches**: 10 (include 2–3 with a personalised 60-second demo). Follow up on week 1.
- **Applications**: 5–7, each with a tailored first paragraph; ask for at least one referral.
- **Posts**: 2 (try the problem post and the technical-decision post for one project).

### Week 3: volume, calls and interview prep

- **Pitches**: 10, plus follow-ups. Run any discovery calls with the script from the outreach lesson and send proposals within the time you promised.
- **Applications**: 5–7.
- **Interview prep**: three practical Python sessions (log parsing, rate limiting, LRU cache, merging intervals, and similar), and one timed RAG system design out loud, using the six steps: requirements, components, data flow, scaling, evals, cost. Prepare a 3-minute deep-dive for each project and your STAR stories.
- **Posts**: 2 (the failure post and the numbers post work well here).

### Week 4: follow through and review

- **Pitches**: 10, plus all outstanding follow-ups (close the loop politely on anything at three or four touches).
- **Applications**: 5–7.
- **Delivery**: if you've won work, deliver it with regular updates, a demo and a proper handover, then ask for a review and a testimonial.
- **Posts**: 2 (a demo post with a soft offer, and an honest "30 days of pitching: what I learned" post).
- **Review** (see below) and set next month's targets.

## Tracking approach

Use one spreadsheet (or a CSV you analyse with Python) with a tab or file for each activity. Minimum columns:

**Pitches**

```
date, channel (upwork/contra/linkedin/email/whatsapp), prospect, niche, gig_type,
personalised_demo (y/n), status (sent/replied/call/proposal/won/lost/no-reply),
follow_up_due, value, notes
```

**Applications**

```
date, company, role, source, referral (y/n), status (applied/screen/interview/offer/rejected/no-reply), notes
```

**Posts**

```
date, platform, format (build-log/lesson/demo/tool/breakdown), hook, impressions, replies, dms, notes
```

Each Friday, spend 20 minutes on a weekly check:

1. Did you hit each target? If not, why?
2. **Reply rate** by channel and by whether you included a personalised demo: replies ÷ pitches sent.
3. Which post formats and hooks led to replies or DMs?
4. Who needs a follow-up next week?
5. One thing to change next week (a better first line, a different niche, a different gig search).

A few lines of Python over the CSV give you the funnel:

```python
import csv
from collections import Counter

with open("pitches.csv", newline="") as f:
    rows = list(csv.DictReader(f))

stages = ["sent", "replied", "call", "proposal", "won"]
reached = Counter()
for r in rows:
    # a pitch that got to "call" also counts as sent and replied
    stage = r["status"] if r["status"] in stages else "sent"  # lost / no-reply still count as sent
    for s in stages[: stages.index(stage) + 1]:
        reached[s] += 1

for s in stages:
    print(f"{s:9} {reached[s]:3}")
```

Divide each stage by the one before it to see where pitches drop off: few replies means the message or targeting needs work; replies but no calls means the ask needs work.

## The 30-day review

Write a one-page review at the end and keep it in your tracker or a private notes doc:

- **Numbers**: pitches, replies, calls, proposals, wins, revenue; applications, screens, interviews; posts, replies, DMs.
- **What worked**: the channel, niche, message or post format with the best results.
- **What didn't**, and your best guess at why.
- **Next month's targets**, adjusted from what you learned. Raise targets for what works; cut what doesn't.

Then keep going. Month two is usually better than month one, because your follow-ups, posts and proof all compound.

## Checklist notes

- "Personalised" means the first lines refer to that client's specific problem. Copy-paste messages don't count towards the target.
- Never take a marketplace client's payments off-platform.
- Use only public information in prospect demos, and say so.
- Keep API keys and billing on clients' accounts, never yours.
