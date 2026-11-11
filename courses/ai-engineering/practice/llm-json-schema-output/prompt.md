# Raw JSON schema output, with a retry

`messages.parse` is the easy path. Underneath, it sends a JSON schema in `output_config`. Here you'll do that by hand, and handle a bad reply.

The starter gives you a `Ticket` model. Write:

```python
TICKET_SCHEMA: dict   # a JSON schema for Ticket

def triage_ticket(client, text: str, model: str = "claude-opus-5-5") -> Ticket | None: ...
```

## `TICKET_SCHEMA`

A JSON schema `dict` for an object with three string properties:

- `category`: one of `"billing"`, `"bug"`, `"feature"`, `"other"` (use `"enum"`)
- `urgency`: one of `"low"`, `"medium"`, `"high"`
- `summary`: any string

It must have `"type": "object"`, list all three in `"required"`, and set `"additionalProperties": False`.

## `triage_ticket`

1. Call `client.messages.create(...)` with `model`, `max_tokens=1000`, one user message containing the ticket text, and
   `output_config={"format": {"type": "json_schema", "schema": TICKET_SCHEMA}}`.
2. Join the reply's text blocks and validate them with `Ticket.model_validate_json(...)`.
3. If validation fails (`pydantic.ValidationError`), try the call **once more**. If the second reply is also invalid, return `None`. Never make more than 2 calls.

## Example

```python
triage_ticket(client, "I was charged twice this month!!")
# Ticket(category='billing', urgency='high', summary='Customer was double-charged')
```

**Check is free and offline.** **Run** uses the real API if your key is set.
