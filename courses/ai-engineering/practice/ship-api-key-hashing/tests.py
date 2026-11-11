import hashlib

from solution import find_owner, generate_api_key, hash_api_key, verify_api_key


def test_generated_keys_are_prefixed_long_and_unique():
    keys = {generate_api_key() for _ in range(50)}
    assert len(keys) == 50, "every generated key must be different"
    k = generate_api_key("sk_test")
    assert k.startswith("sk_test_"), f"key should start with the prefix and an underscore, got {k!r}"
    assert len(k) >= len("sk_test_") + 40, f"use at least 32 random bytes (token_urlsafe(32) is 43 chars), got {k!r}"


def test_hash_is_sha256_hex_and_hides_the_key():
    key = "sk_live_abc123"
    h = hash_api_key(key)
    want = hashlib.sha256(key.encode()).hexdigest()
    assert h == want, f"expected the SHA-256 hex digest {want!r}, got {h!r}"
    assert hash_api_key(key) == h, "hashing must be deterministic"
    assert key not in h, "the stored hash must not contain the key"


def test_verify_accepts_right_key_and_rejects_others():
    key = generate_api_key()
    stored = hash_api_key(key)
    assert verify_api_key(key, stored) is True, "the right key should verify"
    for wrong in (key + "x", key[:-1], "sk_live_guess", key.upper()):
        assert verify_api_key(wrong, stored) is False, f"{wrong!r} must not verify"


def test_verify_rejects_empty_inputs():
    assert verify_api_key("", hash_api_key("")) is False, "an empty key must never verify"
    assert verify_api_key("sk_live_x", "") is False, "an empty stored hash must never verify"


def test_find_owner():
    a, b = generate_api_key(), generate_api_key()
    table = {hash_api_key(a): "acme", hash_api_key(b): "globex"}
    got = (find_owner(a, table), find_owner(b, table), find_owner("nope", table), find_owner(None, table), find_owner("", table))
    want = ("acme", "globex", None, None, None)
    assert got == want, f"expected {want!r}, got {got!r}"
