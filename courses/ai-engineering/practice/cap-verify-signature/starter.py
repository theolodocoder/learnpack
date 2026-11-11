import hashlib
import hmac


def sign(body: bytes, secret: str) -> str:
    """Return 'sha256=' + the hex HMAC-SHA256 of body, keyed with secret."""
    # TODO: hmac.new(key, msg, hashlib.sha256).hexdigest()
    return ""


def verify_signature(body: bytes, header: str | None, secret: str) -> bool:
    """True only if header matches sign(body, secret). Use hmac.compare_digest."""
    # TODO: reject None / missing prefix, then compare in constant time
    return False


if __name__ == "__main__":
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    header = sign(body, "app-secret")
    print(header)
    print(verify_signature(body, header, "app-secret"))         # want True
    print(verify_signature(body + b" ", header, "app-secret"))  # want False
