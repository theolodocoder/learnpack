# A WhatsApp webhook that answers with Claude

Build the core of a WhatsApp support bot for a small business: a FastAPI app with one URL, `/webhook`, that handles Meta's two kinds of request.

The starter gives you `VERIFY_TOKEN`, `SYSTEM_PROMPT`, `FALLBACK`, a `get_client()` dependency, and two module-level stores: `outbox: list[dict]` (stands in for "send this message through the WhatsApp API") and `seen_ids: set[str]`.

## 1. `GET /webhook`: the verification handshake

Meta calls `GET /webhook?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...` when you save your webhook URL. If `hub.mode` is `"subscribe"` and `hub.verify_token` equals `VERIFY_TOKEN`, respond **200** with the challenge as **plain text** (`PlainTextResponse`). Otherwise respond **403**.

Query parameter names contain dots, so use aliases: `mode: Annotated[str | None, Query(alias="hub.mode")] = None`.

## 2. `POST /webhook`: incoming messages

The body looks like this (trimmed):

```json
{"object": "whatsapp_business_account",
 "entry": [{"id": "102290129340398", "changes": [{"field": "messages", "value": {
   "messaging_product": "whatsapp",
   "metadata": {"display_phone_number": "15550783881", "phone_number_id": "106540352242922"},
   "messages": [{"from": "2348031234567", "from_user_id": "NG.1349120865530274",
                 "id": "wamid.ABC", "timestamp": "1739321024",
                 "type": "text", "text": {"body": "How much is the red dress?"}}]}}]}]}
```

For every message in every `entry[].changes[].value.messages[]` (any of these lists may be missing: treat that as empty):

1. Skip it if `type` isn't `"text"`.
2. Skip it if its `id` is already in `seen_ids` (Meta retries deliveries, so duplicates are normal). Otherwise add the id.
3. Call `client.messages.create(model="claude-haiku-5-5", max_tokens=1024, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": <the text body>}])` and join the text blocks of the reply.
4. If the call raises an exception that has a `status_code` attribute (a rate limit, overload, bad request), use `FALLBACK` as the reply instead. Re-raise anything else: that's a bug.
5. Append `{"user": <from_user_id if present, else from>, "text": <reply>}` to `outbox`.

Always return **200** with `{"status": "ok"}`. Status updates (`value` has `"statuses"` instead of `"messages"`) are simply ignored.

`get_client` is a dependency so the tests can swap in a fake: Check is free and offline. Run uses the real API if your key is set.

## Example

```python
client = TestClient(app)
client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "1158201444"}).text
# '1158201444'
client.post("/webhook", json=payload)   # 200 {"status": "ok"}
outbox   # [{"user": "NG.1349120865530274", "text": "The red dress is ₦25,000. ..."}]
```
