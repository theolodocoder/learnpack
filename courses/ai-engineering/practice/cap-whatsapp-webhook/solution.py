from typing import Annotated

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse

VERIFY_TOKEN = "kemi-fashion-verify-2026"
SYSTEM_PROMPT = (
    "You are the WhatsApp assistant for Kemi's Fashion, a clothing shop in Lagos. "
    "Answer questions about products, prices and delivery in one or two short sentences. "
    "If you don't know, say a team member will reply soon."
)
FALLBACK = "Sorry, I'm having trouble right now. A member of our team will reply soon."

outbox: list[dict] = []   # stands in for "send via the WhatsApp API"
seen_ids: set[str] = set()

app = FastAPI()


def get_client():
    return anthropic.Anthropic()


@app.get("/webhook")
def verify(
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
):
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge is not None:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


def answer(client, question: str) -> str:
    try:
        response = client.messages.create(
            model="claude-haiku-5-5", max_tokens=1024, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
        )
    except Exception as e:
        if getattr(e, "status_code", None) is None:
            raise
        return FALLBACK
    return "".join(b.text for b in response.content if b.type == "text")


@app.post("/webhook")
def receive(payload: dict, client=Depends(get_client)):
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("type") != "text" or msg["id"] in seen_ids:
                    continue
                seen_ids.add(msg["id"])
                reply_text = answer(client, msg["text"]["body"])
                outbox.append({"user": msg.get("from_user_id") or msg.get("from"), "text": reply_text})
    return {"status": "ok"}


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    tc = TestClient(app)
    r = tc.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN,
                                   "hub.challenge": "1158201444"})
    print("verify:", r.status_code, r.text)
