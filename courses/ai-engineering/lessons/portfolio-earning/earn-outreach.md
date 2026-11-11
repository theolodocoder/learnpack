# Direct outreach to small businesses

## Why this matters

On marketplaces you compete with hundreds of freelancers for the same post. With direct outreach you find a business that has a problem, show them a solution before they've thought to look for one, and compete with nobody. It's slower per message but the jobs are usually better paid, the clients are more loyal, and one good small-business client can turn into months of retainer work. It's also a sales skill, and with a marketing background you're better placed to learn it than most engineers.

## 1. Pick a niche you can describe in one sentence

Outreach works best when you target one kind of business with one kind of problem. "I build AI for businesses" is too vague to act on. Compare:

- "I help **clinics and pharmacies** answer patient WhatsApp questions from their own price lists and FAQs."
- "I help **accounting firms** turn client invoices and receipts into spreadsheet rows."
- "I help **real-estate agencies** reply to property enquiries instantly with listings that match."
- "I help **schools** answer parent questions about fees, calendars and policies."

A niche lets you reuse one demo, one message template and one set of case studies across many prospects. You can change niche after a month if it doesn't work.

How to choose:

1. **Where do you have access?** Family businesses, your church or mosque community, your university's suppliers, businesses you've done marketing for.
2. **Where is there repetitive text work?** Lots of documents, lots of the same questions, lots of copying between systems.
3. **Who can pay?** A business with staff doing that repetitive work has money tied up in it.
4. **Which of your projects is closest?** Docs chatbot → FAQ-heavy businesses. Extractor → document-heavy businesses. Agent → businesses with multi-step workflows.

## 2. Finding prospects

Sources that work, locally and internationally:

- **Google Maps**: search "accounting firm Lagos", "dental clinic Abuja". You get names, websites, phone numbers and reviews. Reviews often reveal problems ("they never answer the phone").
- **Instagram and WhatsApp Business**: many Nigerian SMEs sell through these. Busy comment sections full of repeated questions ("price?", "do you deliver to Ibadan?") are a clear signal.
- **LinkedIn**: search by job title and industry for owners and operations managers at 5–50 person companies.
- **Directories and associations**: professional bodies, trade associations, startup directories, accelerator portfolios.
- **Your own network**: tell everyone what you build. "Who do you know who spends hours on X?" is a great question.

For international outreach, the same method works with small agencies, clinics and firms in the UK, US, Canada or elsewhere, especially those with a public FAQ, a messy help page or lots of downloadable PDFs on their website.

### Qualify before you write

Spend two minutes per prospect checking for a **visible problem** you can name:

- an FAQ page with 40 questions, or a site full of PDFs (docs chatbot),
- job ads for data-entry or admin staff (extraction or automation),
- slow or missing replies to customer messages (chatbot or triage agent),
- a team page showing several people in support or admin roles.

No visible problem means no personalised message. Skip it.

### Keep a simple tracker

You'll contact dozens of businesses. A spreadsheet works; so does a CSV you check with a few lines of Python. The columns that matter:

```python
import csv
from datetime import date, timedelta
from io import StringIO

tracker = StringIO("""business,contact,channel,niche,problem_seen,sent_on,status
Bright Dental,Dr. Ade,email,clinic,FAQ with 35 questions,2026-11-02,no-reply
Okoro & Co,Mrs. Okoro,linkedin,accounting,hiring data-entry clerk,2026-11-03,replied
HomeFind Realty,Tunde,whatsapp,real-estate,slow replies on Instagram,2026-11-06,no-reply
Kids First School,Bursar,email,school,fees PDF + calendar PDF,2026-11-09,no-reply
""")

today = date(2026, 11, 12)
for row in csv.DictReader(tracker):
    sent = date.fromisoformat(row["sent_on"])
    if row["status"] == "no-reply" and today - sent >= timedelta(days=4):
        print(f"follow up: {row['business']} ({row['channel']}), sent {(today - sent).days} days ago")
# follow up: Bright Dental (email), sent 10 days ago
# follow up: HomeFind Realty (whatsapp), sent 6 days ago
```

The tracker tells you who to follow up with today, and later which niche and channel actually produce replies.

## 3. The message: short, personal, with a 1-minute demo

The single most effective outreach move is a **short, personalised video that shows their problem solved**. For a docs chatbot, that means loading their public FAQ or PDFs into your RAG app, asking it three real questions their customers ask, and recording a 60-second Loom.

Doing this for every prospect sounds like a lot. With your RAG pipeline, it's 15–20 minutes each once you've done it a few times, and the reply rate is far higher than text alone. Do it only for prospects you've qualified.

> **Note:** Use only information the business has published publicly, and say so in the message. Don't scrape private data, and don't present the demo as a finished product.

The message itself should be readable in 20 seconds:

```
Subject: Your FAQ, answered instantly (1-min video)

Hi Dr. Ade,

I noticed Bright Dental's FAQ page has over 30 questions, and a couple of your
Google reviews mention it's hard to get through on the phone.

I loaded your public FAQ and price list into a small assistant I built. Here's a
60-second video of it answering three questions patients often ask, with the
source for each answer: https://loom.com/share/...

If it's useful, I could set up a version for your website or WhatsApp. Would a
15-minute call next week make sense?

Ada Obi
AI engineer, Lagos · ada-obi.dev
```

Why it works:

- **Personal first line**: proof you looked at *their* business, not a list.
- **The problem in their terms**: phone calls, not "RAG".
- **Proof, not promises**: the video shows their own content working.
- **A small ask**: a 15-minute call, not "hire me".
- **No attachments, no long bio, no price.** Price comes after the call.

Channel matters. Email works for clinics, firms and international businesses. LinkedIn DMs work for owners active there. WhatsApp and Instagram DMs are often the most direct route to Nigerian SMEs, but keep the first message even shorter and respectful of their time. Don't add people to broadcast lists or groups without asking.

## 4. Following up

Most replies come from follow-ups, not first messages. People are busy, not uninterested. A simple sequence:

| When | Message |
|---|---|
| Day 0 | The personalised message with the video |
| Day 4–5 | "Just bumping this in case it got buried. Happy to send the assistant link so you can try it yourself." |
| Day 10–12 | Add value: "I also noticed your fees PDF is a scanned image, so search engines and assistants can't read it. Here's a quick fix: …" |
| Day 20 | Close the loop politely: "I'll stop following up here. If answering patient questions ever becomes a priority, I'm happy to help." |

Then stop. Three or four touches is persistent; ten is spam. The polite close-out often gets a reply because it removes pressure.

## 5. The discovery call

When someone agrees to talk, the call has one purpose: understand their problem well enough to propose a scoped solution with a price. Talk less than they do. A 15–25 minute script:

**1. Open (1 min).** "Thanks for making time. I'd love to understand how questions and documents are handled today, then I'll tell you honestly if and how I can help. Sound good?"

**2. Current situation (5–8 min).**
- "Walk me through what happens when a patient sends a question today."
- "Who answers? How many questions a day or week, roughly?"
- "Where does the information they use live?"

**3. Pain and cost (3–5 min).**
- "What's the most annoying part of that?"
- "What happens when a question goes unanswered?"
- "Roughly how many hours a week does that take your team?"

**4. What success looks like (3 min).**
- "If this worked perfectly in three months, what would be different?"
- "How would you know it's working?" (This becomes your acceptance criteria.)

**5. Constraints (2–3 min).**
- "Is there anything it must never get wrong?" (Prices, medical advice, legal terms: important for guardrails.)
- "Who else is involved in deciding?"
- "Have you set aside a budget for this, or would it help if I gave you a couple of options?"

**6. Next step (2 min).** "Based on this, I'll send you a one-page proposal with two options and prices by Thursday. Does that work?"

After the call, send the proposal within the promised time: the problem in their words, two packages (anchoring with the fuller one first, as covered in the freelance lesson), deliverables, timeline, running costs and acceptance criteria.

> **Try it:** Role-play the discovery call with a friend acting as a pharmacy owner. Record it. Count how many minutes you spoke versus them. Aim for them talking at least 60% of the time.

## 6. From a first small project to a retainer

Small businesses are cautious with someone new. Make the first yes easy:

- **Start small and fixed-price.** A pilot: "chatbot on your FAQ and price list, on your website only, two weeks." Low risk for them, a fast win for you.
- **Measure from day one.** Log questions answered, questions escalated and the time saved, so you can show results after a month.
- **Report results.** A one-page monthly summary: "412 questions answered, 37 handed to staff, top 5 unanswered topics."

A retainer is a fixed monthly fee for ongoing work. LLM systems genuinely need it, so it's an honest offer, not an upsell:

- documents and prices change, so the knowledge base needs updating,
- new failure cases appear, so the eval set grows and prompts get fixed,
- models are updated or deprecated, so the system needs testing on new versions,
- API costs need monitoring,
- the client will want small improvements and new channels.

How to propose it, at the end of the pilot:

```
The assistant answered 412 questions this month, and the top unanswered topic
was insurance coverage. I'd suggest a monthly plan: I keep the documents current,
review failures weekly, add answers for new topics, monitor costs and handle any
model updates. That's $X/month, and you can cancel with 30 days' notice.
```

Two or three retainers make your income predictable while you keep doing project work and studying.

## Common mistakes

- **Mass messaging.** Copy-paste messages to 200 businesses get ignored or reported. Ten researched messages a week beat 200 generic ones.
- **Leading with technology.** "I build RAG pipelines with vector databases" means nothing to a dentist. Talk about patients, phone calls and hours saved.
- **Long first messages.** If it doesn't fit on a phone screen, cut it.
- **Quoting a price in the first message.** You don't know the scope yet.
- **No follow-up.** Most replies come on the second or third touch.
- **Talking too much on the call.** Your job is to listen, then summarise their problem better than they could.
- **Using private data in demos.** Use only what the business has published, and say so.
- **Ending a pilot without a next step.** Always show results and propose the ongoing plan.

## Recap

- Pick a niche you can describe in one sentence, matched to one of your projects.
- Find prospects on Google Maps, Instagram/WhatsApp, LinkedIn and through your network, and qualify each one by a visible problem.
- Send a short, personalised message with a 60-second demo using their public content, and a small ask.
- Follow up three or four times over about three weeks, then close the loop politely.
- Run discovery calls by asking and listening: situation, pain, success, constraints, next step.
- Start with a small fixed-price pilot, measure results, then propose an honest monthly retainer.
