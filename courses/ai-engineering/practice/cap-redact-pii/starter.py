import hashlib
import re

# TODO: write the two patterns
EMAIL = re.compile(r"$^")   # matches nothing yet
PHONE = re.compile(r"$^")   # matches nothing yet


def redact(text: str) -> str:
    """Replace emails with [EMAIL] and Nigerian mobile numbers with [PHONE]."""
    # TODO: substitute both patterns
    return text


def log_entry(user_id: str, text: str, salt: str) -> dict:
    """{'user': first 12 hex chars of sha256(salt + user_id), 'text': redacted text}."""
    # TODO
    return {"user": user_id, "text": text}


if __name__ == "__main__":
    print(redact("Call me on 0803 123 4567 or mail ada.obi@gmail.com"))
    print(redact("Order #100234 is ₦25,000, paid by +2348031234567"))
    print(log_entry("2348031234567", "my email is ada@x.ng", salt="s3cret"))
