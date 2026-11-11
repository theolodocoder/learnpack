import hashlib

from solution import log_entry, redact


def test_redacts_emails():
    got = redact("Mail ada.obi@gmail.com or sales+ng@kemi-fashion.com.ng today")
    want = "Mail [EMAIL] or [EMAIL] today"
    assert got == want, f"expected {want!r}, got {got!r}"


def test_redacts_local_nigerian_numbers():
    for raw in ["08031234567", "0803 123 4567", "0701-234-5678", "09012345678", "0811 234 5678"]:
        got = redact(f"call {raw} now")
        assert got == "call [PHONE] now", f"{raw!r} should become [PHONE], got {got!r}"


def test_redacts_international_nigerian_numbers():
    for raw in ["+2348031234567", "2348031234567", "+234 803 123 4567", "+234-803-123-4567", "+234 7012345678"]:
        got = redact(f"call {raw} now")
        assert got == "call [PHONE] now", f"{raw!r} should become [PHONE], got {got!r}"


def test_leaves_other_numbers_alone():
    for keep in ["Order #100234 is ₦25,000", "Founded in 2026", "Ref 0803123456", "Code 080312345678901",
                 "Landline 01 234 5678", "Pay 08531234567"]:
        got = redact(keep)
        assert got == keep, f"{keep!r} has no phone number or email and should be unchanged, got {got!r}"


def test_mixed_message():
    got = redact("Order #100234 is ₦25,000, paid by +2348031234567. Receipt to ada@x.ng")
    want = "Order #100234 is ₦25,000, paid by [PHONE]. Receipt to [EMAIL]"
    assert got == want, f"expected {want!r}, got {got!r}"


def test_log_entry_pseudonymises_the_user():
    entry = log_entry("2348031234567", "my number is 08031234567", salt="s3cret")
    want_user = hashlib.sha256(b"s3cret2348031234567").hexdigest()[:12]
    assert entry == {"user": want_user, "text": "my number is [PHONE]"}, \
        f"expected {{'user': {want_user!r}, 'text': 'my number is [PHONE]'}}, got {entry!r}"
    other = log_entry("2348031234567", "hi", salt="different")
    assert other["user"] != want_user, "a different salt should give a different pseudonym"
