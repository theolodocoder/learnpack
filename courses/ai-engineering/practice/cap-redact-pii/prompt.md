# Redact personal data before you log it

Logging real conversations is how you improve your product, but a log full of phone numbers and email addresses is a liability. Redact before you write anything down, and pseudonymise the user id so you can still group a user's messages without storing who they are.

Write two functions:

```python
def redact(text: str) -> str:
def log_entry(user_id: str, text: str, salt: str) -> dict:
```

## `redact`

Replace every email address with `[EMAIL]` and every Nigerian mobile number with `[PHONE]`. Leave everything else alone.

Nigerian mobile numbers have 11 digits starting with `0`, then `7`, `8` or `9`, then `0` or `1` (for example `08031234567`, `0701 234 5678`). In international form the leading `0` becomes `+234` or `234`: `+2348031234567`, `+234 803 123 4567`, `234-803-123-4567`. Single spaces or dashes may appear between any of the digits after the prefix (and between `+234` and the rest).

Don't redact other numbers: an order number like `#100234`, an amount like `₦25,000`, a year, or a 10-digit number. A number glued to more digits (`080312345678901`) isn't a phone number either.

## `log_entry`

Return `{"user": <pseudonym>, "text": redact(text)}`, where the pseudonym is the first 12 hex characters of `sha256((salt + user_id).encode())`. The same user and salt always give the same pseudonym; the raw id never appears in the entry.

## Example

```python
redact("Call me on 0803 123 4567 or mail ada.obi@gmail.com")
# 'Call me on [PHONE] or mail [EMAIL]'
redact("Order #100234 is ₦25,000, paid by +2348031234567")
# 'Order #100234 is ₦25,000, paid by [PHONE]'
log_entry("2348031234567", "my email is ada@x.ng", salt="s3cret")
# {'user': '…12 hex chars…', 'text': 'my email is [EMAIL]'}
```
