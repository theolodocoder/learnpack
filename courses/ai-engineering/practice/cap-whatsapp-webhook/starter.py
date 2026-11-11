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
    # TODO: return PlainTextResponse(challenge) if mode == "subscribe" and token == VERIFY_TOKEN, else 403
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
def receive(payload: dict, client=Depends(get_client)):
    # TODO: loop over entry -> changes -> value -> messages (use .get(..., []) for missing lists)
    # TODO: skip non-text messages and ids already in seen_ids
    # TODO: call Claude; on an exception with status_code use FALLBACK
    # TODO: outbox.append({"user": ..., "text": ...})
    return {"status": "ok"}


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    tc = TestClient(app)
    r = tc.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN,
                                   "hub.challenge": "1158201444"})
    print("verify:", r.status_code, r.text)
    payload = {"object": "whatsapp_business_account", "entry": [{"id": "1", "changes": [{"field": "messages", "value": {
        "messages": [{"from": "2348031234567", "id": "wamid.DEMO1", "type": "text",
                      "text": {"body": "Do you deliver to Ibadan?"}}]}}]}]}
    try:
        print("post:", tc.post("/webhook", json=payload).json())
        print("outbox:", outbox)
    except Exception as e:  # e.g. no ANTHROPIC_API_KEY set
        print(f"Calling Claude failed ({type(e).__name__}). Set ANTHROPIC_API_KEY to try the real API; Check works offline.")
