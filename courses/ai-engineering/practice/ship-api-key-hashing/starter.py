import hashlib
import hmac
import secrets


def generate_api_key(prefix: str = "sk_live") -> str:
    """A new random key like 'sk_live_<43 url-safe characters>'. Shown to the user once."""
    # TODO: use secrets.token_urlsafe(32)
    return ""


def hash_api_key(key: str) -> str:
    """The SHA-256 hex digest of the key: this is what you store."""
    # TODO
    return ""


def verify_api_key(key: str, stored_hash: str) -> bool:
    """True if `key` hashes to `stored_hash`. Empty key or hash -> False. Constant-time compare."""
    # TODO: hmac.compare_digest
    return False


def find_owner(key: str | None, keys_by_hash: dict[str, str]) -> str | None:
    """Return the owner for `key` from a {stored_hash: owner} table, or None."""
    # TODO
    return None


if __name__ == "__main__":
    key = generate_api_key()
    stored = hash_api_key(key)
    print("give the user:", key)
    print("store:        ", stored)
    print("verify right: ", verify_api_key(key, stored))
    print("verify wrong: ", verify_api_key("sk_live_guess", stored))
    print("owner:        ", find_owner(key, {stored: "acme-corp"}))
