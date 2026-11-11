import hashlib
import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# A leading 0 or a +234/234 prefix, then 7/8/9, then 0/1, then 8 more digits.
# Single spaces or dashes are allowed between digits; no digit may touch either end.
PHONE = re.compile(r"(?<!\d)(?:\+?234[ -]?|0)[789][ -]?[01](?:[ -]?\d){8}(?!\d)")


def redact(text: str) -> str:
    """Replace emails with [EMAIL] and Nigerian mobile numbers with [PHONE]."""
    text = EMAIL.sub("[EMAIL]", text)
    return PHONE.sub("[PHONE]", text)


def log_entry(user_id: str, text: str, salt: str) -> dict:
    """{'user': first 12 hex chars of sha256(salt + user_id), 'text': redacted text}."""
    pseudonym = hashlib.sha256((salt + user_id).encode()).hexdigest()[:12]
    return {"user": pseudonym, "text": redact(text)}


if __name__ == "__main__":
    print(redact("Call me on 0803 123 4567 or mail ada.obi@gmail.com"))
