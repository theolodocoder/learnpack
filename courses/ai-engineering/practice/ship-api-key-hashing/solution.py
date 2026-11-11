import hashlib
import hmac
import secrets


def generate_api_key(prefix: str = "sk_live") -> str:
    """A new random key, shown to the user once."""
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """What you store in the database instead of the key."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, stored_hash: str) -> bool:
    if not key or not stored_hash:
        return False
    return hmac.compare_digest(hash_api_key(key), stored_hash)


def find_owner(key: str | None, keys_by_hash: dict[str, str]) -> str | None:
    """Look up who owns `key`, given a mapping of stored hash -> owner."""
    if not key:
        return None
    return keys_by_hash.get(hash_api_key(key))


if __name__ == "__main__":
    key = generate_api_key()
    stored = hash_api_key(key)
    print("give the user:", key)
    print("store:        ", stored)
    print("verify right: ", verify_api_key(key, stored))
    print("verify wrong: ", verify_api_key("sk_live_guess", stored))
    print("owner:        ", find_owner(key, {stored: "acme-corp"}))
