from fastapi.testclient import TestClient

import solution
from fake_llm import BadRequest, FakeAnthropic, Overloaded, reply, text
from solution import FALLBACK, SYSTEM_PROMPT, VERIFY_TOKEN, app, get_client

tc = TestClient(app)


def message(msg_id: str, body: str = "How much is the red dress?", type_: str = "text", **extra) -> dict:
    m = {"from": "2348031234567", "id": msg_id, "timestamp": "1739321024", "type": type_, **extra}
    if type_ == "text":
        m["text"] = {"body": body}
    return m


def payload(*messages, statuses=None) -> dict:
    value = {"messaging_product": "whatsapp",
             "metadata": {"display_phone_number": "15550783881", "phone_number_id": "106540352242922"}}
    if messages:
        value["messages"] = list(messages)
    if statuses:
        value["statuses"] = statuses
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "102290129340398", "changes": [{"field": "messages", "value": value}]}]}


def post(body: dict, script: list):
    solution.outbox.clear()
    solution.seen_ids.clear()
    fake = FakeAnthropic(script)
    app.dependency_overrides[get_client] = lambda: fake
    try:
        r = tc.post("/webhook", json=body)
    finally:
        app.dependency_overrides.clear()
    return r, fake


def test_verification_handshake():
    r = tc.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "1158201444"})
    assert r.status_code == 200, f"a correct verify token should get 200, got {r.status_code}"
    assert r.text == "1158201444", f"respond with the bare challenge as plain text, got {r.text!r}"
    r = tc.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "1158201444"})
    assert r.status_code == 403, f"a wrong verify token should get 403, got {r.status_code}"
    r = tc.get("/webhook", params={"hub.mode": "unsubscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "1"})
    assert r.status_code == 403, f"hub.mode must be 'subscribe', got {r.status_code}"


def test_answers_a_text_message_with_claude():
    r, fake = post(payload(message("wamid.A1", from_user_id="NG.1349120865530274")),
                   [reply(text("The red dress is ₦25,000."))])
    assert r.status_code == 200 and r.json() == {"status": "ok"}, f"expected 200 {{'status': 'ok'}}, got {r.status_code} {r.text}"
    want = [{"user": "NG.1349120865530274", "text": "The red dress is ₦25,000."}]
    assert solution.outbox == want, f"expected outbox {want!r} (from_user_id preferred over from), got {solution.outbox!r}"
    call = fake.calls[0]
    assert call.get("system") == SYSTEM_PROMPT, "send SYSTEM_PROMPT as the system prompt"
    assert call.get("messages") == [{"role": "user", "content": "How much is the red dress?"}], \
        f"send the message text as the user turn, got {call.get('messages')!r}"


def test_falls_back_to_from_when_no_user_id():
    post(payload(message("wamid.B1")), [reply(text("Yes, we deliver."))])
    assert solution.outbox == [{"user": "2348031234567", "text": "Yes, we deliver."}], \
        f"without from_user_id, use from; got {solution.outbox!r}"


def test_duplicate_deliveries_are_answered_once():
    body = payload(message("wamid.C1"))
    solution.outbox.clear()
    solution.seen_ids.clear()
    fake = FakeAnthropic([reply(text("Answer once."))])
    app.dependency_overrides[get_client] = lambda: fake
    try:
        for _ in range(3):
            r = tc.post("/webhook", json=body)
            assert r.status_code == 200, f"a duplicate delivery must still get 200 (or Meta keeps retrying), got {r.status_code}"
    finally:
        app.dependency_overrides.clear()
    assert len(fake.calls) == 1, f"the same message id should call Claude once, it was called {len(fake.calls)} times"
    assert len(solution.outbox) == 1, f"expected one reply in the outbox, got {solution.outbox!r}"


def test_llm_errors_send_the_fallback():
    r, _ = post(payload(message("wamid.D1"), message("wamid.D2", "Open on Sunday?")), [Overloaded(), BadRequest()])
    assert r.status_code == 200, f"LLM errors must not fail the webhook, got {r.status_code}"
    texts = [m["text"] for m in solution.outbox]
    assert texts == [FALLBACK, FALLBACK], f"expected the fallback for both messages, got {texts!r}"


def test_ignores_status_updates_and_non_text_messages():
    statuses = [{"id": "wamid.OUT1", "status": "delivered", "timestamp": "1739321030", "recipient_id": "2348031234567"}]
    r, fake = post(payload(message("wamid.E1", type_="image"), statuses=statuses), [])
    assert r.status_code == 200, f"expected 200, got {r.status_code}"
    assert fake.calls == [] and solution.outbox == [], "status updates and non-text messages should not call Claude or reply"
    r, _ = post({"object": "whatsapp_business_account", "entry": [{"id": "1", "changes": [{"field": "messages", "value": {}}]}]}, [])
    assert r.status_code == 200, f"a value with no messages should still get 200, got {r.status_code}"
