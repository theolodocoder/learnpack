# Messaging channels: WhatsApp, Telegram and email

## Why this matters

Your users already have WhatsApp open all day. Asking a shop's customers to visit a website and type into a chat box loses most of them; answering them in the app they're already using keeps all of them. Messaging channels also share one engineering pattern that you'll meet in every integration job: **webhooks**. The provider calls your server when something happens. You must prove the call is genuine, handle the same event arriving twice, and answer quickly. Get those three right and WhatsApp, Telegram, email, Stripe and GitHub integrations all look the same.

## 1. Choosing a channel

| Channel | Setup effort | Good for | Watch out for |
|---|---|---|---|
| **Telegram bot** | Minutes: message @BotFather, get a token | Prototyping a chat product today; tech-savvy users | Fewer of your target users are on it than on WhatsApp |
| **WhatsApp Cloud API** | Hours for a test number; days or weeks for a real business number (business verification, display name approval) | Small businesses and customers in Nigeria and most of the world | Meta's rules: 24-hour window, templates, opt-in, per-message pricing, AI policy |
| **Email** | An hour with a provider | Meeting notes, job applications, anything long or with attachments | Deliverability (SPF, DKIM, DMARC), slower back-and-forth |

A good plan for the WhatsApp shop bot: build your core logic behind a plain function `answer(user_id, text) -> str`, prototype it on Telegram (or a web chat) in week 9 while WhatsApp setup is in progress, then plug the same function into the WhatsApp webhook. The channel is an adapter; the product is the function.

## 2. Webhooks: the three rules

A **webhook** is an HTTP request the provider sends to a URL you registered, whenever an event happens: a user sent a message, a message was delivered, an email arrived. Three rules apply to all of them.

1. **Verify it's genuine.** Your webhook URL is public. Anyone can POST fake "messages" to it and make you spend tokens or send replies. Providers sign requests (an HMAC of the body with a shared secret) or include a secret header. Check it before doing anything.
2. **Expect duplicates.** If your server is slow, returns an error, or the network hiccups, the provider **retries**. Meta's docs say failed WhatsApp deliveries are retried immediately and then with decreasing frequency for up to 7 days, and that you should deduplicate. Telegram also repeats unsuccessful requests. Your handler must be **idempotent**: processing the same event twice must have the same effect as processing it once.
3. **Acknowledge fast.** Return `200` as soon as you've verified and stored the event, then do the slow work (calling Claude, sending the reply) afterwards. If you call Claude first and it takes 20 seconds, the provider may time out and retry, and the user gets two answers.

## 3. WhatsApp Cloud API: the concepts

The **WhatsApp Business Platform** has an API hosted by Meta called the **Cloud API**. You don't run any WhatsApp software yourself; you make HTTPS calls to Meta's Graph API and receive webhooks.

**Setup, in Meta's terms.** You create a Meta app with the *Connect with customers through WhatsApp* use case in the App Dashboard, connected to a business portfolio and a WhatsApp Business Account. The API Setup page gives you a **test phone number**, its **phone number ID**, and a **temporary access token** so you can send test messages straight away. For production you add the business's real number, complete business verification, and use a long-lived **system user access token**. Keep every token and the **app secret** in environment variables.

**Receiving messages: the webhook.** In the dashboard's Configuration panel you set a **Callback URL** (your `https://…/webhook`) and a **Verify token** (any string you choose). Meta then:

- sends a **GET** to verify the URL: `?hub.mode=subscribe&hub.challenge=<random>&hub.verify_token=<your token>`. If the token matches yours, respond `200` with the `hub.challenge` value as the body. Anything else and Meta won't send you webhooks.
- sends a **POST** for each event, with a JSON body and an `X-Hub-Signature-256: sha256=<hex>` header. The hex is the HMAC-SHA256 of the raw body, keyed with your **app secret**.

A text message arrives like this (trimmed to the parts you'll use):

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "<WHATSAPP_BUSINESS_ACCOUNT_ID>",
    "changes": [{
      "field": "messages",
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {"display_phone_number": "15550783881", "phone_number_id": "106540352242922"},
        "contacts": [{"profile": {"name": "Ada"}, "wa_id": "2348031234567", "user_id": "<BSUID>"}],
        "messages": [{
          "from": "2348031234567", "from_user_id": "<BSUID>",
          "id": "wamid.HBgLMTY1MDM4Nzk0MzkVAgASGBQzQUFERjg0NDEzNDdFODU3MUMxMAA=",
          "timestamp": "1739321024", "type": "text",
          "text": {"body": "Do you deliver to Ibadan?"}
        }]
      }
    }]
  }]
}
```

Things to notice:

- The same webhook field carries **status updates** for messages *you* sent (sent, delivered, read) under `value.statuses` instead of `value.messages`. Ignore them or use them for analytics, but don't reply to them.
- `type` can be `text`, `image`, `audio`, `document`, `interactive`, and more. Handle `text` and reply politely to the rest ("I can only read text messages for now").
- `id` (the `wamid…`) is the message's unique id: your idempotency key.
- Meta now gives users **business-scoped user IDs** (`user_id` / `from_user_id`) and lets users adopt usernames. When a user's phone number isn't available, `from` and `wa_id` are left out, so key your users table on the BSUID, falling back to the phone number.

**Sending messages.** Replies go out through the Graph API: `POST https://graph.facebook.com/<API_VERSION>/<PHONE_NUMBER_ID>/messages` with your access token. A text reply:

```python
import httpx

def send_text(client: httpx.Client, phone_number_id: str, to: str, body: str) -> str:
    r = client.post(
        f"/{phone_number_id}/messages",
        json={"messaging_product": "whatsapp", "recipient_type": "individual",
              "to": to, "type": "text", "text": {"body": body[:4096]}},
    )
    r.raise_for_status()
    return r.json()["messages"][0]["id"]   # the wamid of the message you sent

# In production:
# client = httpx.Client(base_url="https://graph.facebook.com/v27.0",
#                       headers={"Authorization": f"Bearer {os.environ['WHATSAPP_TOKEN']}"}, timeout=15)
```

Text bodies are limited to 4,096 characters. (Use the Graph API version the docs currently show; `v27.0` was current when this was written. To send to a user who has only a BSUID, the docs show a `recipient` field in place of `to`.)

**The 24-hour customer service window.** This is the rule that shapes every WhatsApp product. When a user messages (or calls) the business, a **24-hour customer service window** opens, and each new message from them resets it. Inside the window you can send free-form **service messages**: any text, image or document. Once it closes, you can only send pre-approved **template messages**. In practice:

- A support bot replying to customers lives comfortably inside the window.
- "Your order has shipped" two days later, or a weekly reminder, needs a **template**: a message format you submit for approval, in a category (**marketing**, **utility** or **authentication**), with placeholders like `{{1}}` for the name.
- You may only message users who have **opted in** to hear from the business.

**Pricing and policy.** Meta charges per delivered message, with rates by category and country. As of 1 October 2026 that includes service messages, which had been free; check the current pricing page for your market before you promise a business a monthly cost. Also note Meta's WhatsApp Business Solution Terms (updated 15 January 2026): providers of **general-purpose AI assistants** are restricted from offering them on the platform in most markets. A bot that answers questions about one business's products, orders and policies, which is what your capstone builds, is the ordinary customer-support use case. A "chat with an AI about anything" bot on WhatsApp is not.

> **Note:** Meta's docs, rules and prices change often, and old tutorials go stale fast. When a video or blog post disagrees with developers.facebook.com, the docs win.

## 4. Verifying the signature

HMAC (hash-based message authentication code) combines a secret key and a message into a fixed-length code. Only someone with the key can produce the right code, and changing a single byte of the message changes the code completely. Python's `hmac` module does it:

```python
import hashlib
import hmac

secret = "my-app-secret"
body = b'{"object":"whatsapp_business_account","entry":[]}'
expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
print(expected[:20])   # sha256=…  (64 hex characters in total after the prefix)

received = expected     # in real life: request.headers.get("X-Hub-Signature-256")
print(hmac.compare_digest(received, expected))  # True
```

Two details matter:

- **Sign the raw bytes.** In FastAPI, read them with `await request.body()` *before* parsing. If you parse the JSON and dump it again, whitespace and key order may differ and the signature won't match.
- **Compare with `hmac.compare_digest`, not `==`.** String `==` returns as soon as it finds a different character, so an attacker timing many requests can learn the right signature one character at a time. `compare_digest` takes the same time regardless.

In a FastAPI route:

```python
import json
import os

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

app = FastAPI()

@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks):
    body = await request.body()
    if not verify_signature(body, request.headers.get("X-Hub-Signature-256"), os.environ["META_APP_SECRET"]):
        raise HTTPException(status_code=403)
    payload = json.loads(body)
    background.add_task(process, payload)   # runs after the response is sent
    return {"status": "ok"}
```

`BackgroundTasks` runs `process` after the 200 has gone out, which satisfies rule 3. It runs in the same process, so if the server restarts mid-task the work is lost. For a capstone with a few users that's acceptable, especially since you store the message first. A larger system would put the event on a queue.

## 5. Idempotency

The simplest idempotency is "have I seen this id before?". In memory, a set is enough for a demo:

```python
seen: set[str] = set()

def handle_once(message_id: str) -> bool:
    if message_id in seen:
        return False      # duplicate: do nothing
    seen.add(message_id)
    return True

print(handle_once("wamid.A"), handle_once("wamid.A"))  # True False
```

But memory is wiped on every deploy or restart, and if you run two server processes they each have their own set. Use the database instead and let a `UNIQUE` constraint do the work. It's atomic, so even two simultaneous deliveries can't both win:

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE inbound (external_id TEXT PRIMARY KEY, body TEXT)")

def store_once(external_id: str, body: str) -> bool:
    cur = db.execute("INSERT OR IGNORE INTO inbound (external_id, body) VALUES (?, ?)", (external_id, body))
    db.commit()
    return cur.rowcount == 1     # 1 = new, 0 = already there

print(store_once("wamid.A", "hi"), store_once("wamid.A", "hi"))  # True False
```

(In Postgres the equivalent is `INSERT … ON CONFLICT (external_id) DO NOTHING`.) Store first, check the result, and only then call Claude and reply.

> **Try it:** The WhatsApp webhook exercise puts all of this together: the verification handshake, parsing the payload, skipping duplicates, calling Claude through the fake client, and sending a fallback message when the model fails.

## 6. Telegram: the fastest prototype

Telegram's Bot API is the easiest channel to start with:

1. Message **@BotFather** in Telegram, send `/newbot`, and get a token like `123456:ABC…`. Keep it secret.
2. Receive messages with **`getUpdates`** (long polling: your script asks Telegram for new messages, no public URL needed) or with **`setWebhook`** (Telegram POSTs to your HTTPS URL). The two are mutually exclusive, and Telegram keeps undelivered updates for up to 24 hours.
3. Reply with **`sendMessage`**.

A complete polling bot fits on one screen:

```python
import os
import httpx

API = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}"

def run(answer):                       # answer(user_id: str, text: str) -> str
    offset = 0
    with httpx.Client(timeout=40) as client:
        while True:
            updates = client.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 30}).json()["result"]
            for update in updates:
                offset = update["update_id"] + 1      # confirms this update; it won't be sent again
                msg = update.get("message")
                if msg and "text" in msg:
                    reply = answer(str(msg["chat"]["id"]), msg["text"])
                    client.post(f"{API}/sendMessage", json={"chat_id": msg["chat"]["id"], "text": reply})
```

For production, switch to a webhook: call `setWebhook` with your URL and a `secret_token`. Telegram then sends that token in an `X-Telegram-Bot-Api-Secret-Token` header on every request; compare it with `hmac.compare_digest`. Each update has an increasing **`update_id`**, which the docs suggest using to ignore repeated updates: your idempotency key.

## 7. Email in and out

Email suits the meeting-notes and job-application products: people forward a transcript or job post to an address and get a reply.

**Outbound** is easy with the standard library. Build the message with `email.message.EmailMessage` and send it through your provider's SMTP server (or its HTTP API):

```python
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "Notes Bot <notes@yourdomain.com>"
msg["To"] = "team@example.com"
msg["Subject"] = "Action items: Monday stand-up"
msg.set_content("1. Ada: send the budget by Friday\n2. Bayo: book the venue by Wednesday")
print(msg["Subject"])  # Action items: Monday stand-up

# Sending (needs real credentials):
# import smtplib
# with smtplib.SMTP("smtp.yourprovider.com", 587) as s:
#     s.starttls(); s.login(user, password); s.send_message(msg)
```

**Deliverability** decides whether that lands in the inbox or spam. Send from your own domain, and set up **SPF**, **DKIM** and **DMARC** DNS records as your provider instructs. Gmail's sender guidelines require them for bulk senders. Don't send from a free Gmail address through a script.

**Inbound** email is easiest through a provider's "inbound parse" feature (Postmark, SendGrid, Mailgun and others): they receive mail for your domain and POST it to your webhook as JSON, with sender, subject, text body and attachments. The same three webhook rules apply. Each provider verifies requests in its own way (a signature header, basic auth on the URL, or a secret in the path), so read their docs. Email also needs **loop protection**: never auto-reply to an auto-reply (check headers like `Auto-Submitted`), or two bots will email each other forever.

## Common mistakes

- **Not verifying webhook requests.** Anyone can then make your bot spend money or message people.
- **Verifying a re-serialised body.** Sign and check the exact raw bytes you received.
- **`==` for signatures.** Use `hmac.compare_digest`.
- **Calling the LLM before returning 200.** Slow responses cause retries, and retries cause duplicate replies.
- **In-memory dedupe in production.** It's wiped on restart; use a unique constraint.
- **Replying to status updates or your own messages.** Only reply to inbound user messages.
- **Ignoring the 24-hour window.** Free-form messages outside it fail; plan templates for anything proactive.
- **Building a general-purpose AI chat on WhatsApp.** Keep the bot about the business.
- **Trusting an old tutorial over Meta's docs.** The platform changes every few months.

## Recap

- The channel is an adapter around one `answer(user_id, text)` function. Prototype on Telegram or web while WhatsApp setup runs.
- Webhooks: verify, deduplicate, acknowledge fast, then process.
- WhatsApp Cloud API: GET verification with your verify token; POSTs signed with `X-Hub-Signature-256` (HMAC-SHA256 of the raw body with the app secret); replies via `POST /<PHONE_NUMBER_ID>/messages`.
- Free-form replies only inside the 24-hour customer service window; templates (marketing, utility, authentication) outside it; per-message pricing; opt-in required.
- Idempotency: a `UNIQUE` message id and `INSERT OR IGNORE` / `ON CONFLICT DO NOTHING`.
- Telegram: BotFather token, `getUpdates` or `setWebhook` with a secret token, `update_id` for dedupe. Email: `EmailMessage` out, inbound parse webhooks in, SPF/DKIM/DMARC for deliverability.
