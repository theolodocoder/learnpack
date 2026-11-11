import hashlib
import hmac


def sign(body: bytes, secret: str) -> str:
    """Return 'sha256=' + the hex HMAC-SHA256 of body, keyed with secret."""
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, header: str | None, secret: str) -> bool:
    """True only if header matches sign(body, secret). Use hmac.compare_digest."""
    if not header or not header.startswith("sha256="):
        return False
    return hmac.compare_digest(header, sign(body, secret))


if __name__ == "__main__":
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    print(verify_signature(body, sign(body, "app-secret"), "app-secret"))
