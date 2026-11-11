import hashlib
import hmac
import inspect

import solution
from solution import sign, verify_signature

BODY = b'{"object":"whatsapp_business_account","entry":[{"id":"102290129340398","changes":[]}]}'
SECRET = "app-secret"


def test_sign_matches_hmac_sha256():
    want = "sha256=" + hmac.new(SECRET.encode(), BODY, hashlib.sha256).hexdigest()
    got = sign(BODY, SECRET)
    assert got == want, f"expected {want!r}, got {got!r}"


def test_accepts_a_genuine_signature():
    assert verify_signature(BODY, sign(BODY, SECRET), SECRET) is True, "a correctly signed body should verify"


def test_rejects_a_tampered_body():
    header = sign(BODY, SECRET)
    tampered = BODY.replace(b"102290129340398", b"999999999999999")
    assert verify_signature(tampered, header, SECRET) is False, "a changed body must not verify"
    assert verify_signature(BODY + b" ", header, SECRET) is False, "even one extra byte must not verify"


def test_rejects_wrong_secret_and_bad_headers():
    header = sign(BODY, SECRET)
    assert verify_signature(BODY, header, "other-secret") is False, "a signature made with another secret must not verify"
    hex_only = header.removeprefix("sha256=")
    for bad in (None, "", hex_only, "sha1=" + hex_only, "sha256="):
        assert verify_signature(BODY, bad, SECRET) is False, f"header {bad!r} should be rejected"


def test_uses_constant_time_compare():
    src = inspect.getsource(solution.verify_signature)
    assert "compare_digest" in src, "compare signatures with hmac.compare_digest, not =="
