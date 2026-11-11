import re
from urllib.parse import urlsplit

_TAG = re.compile(r"<(/?untrusted_content)", re.IGNORECASE)


def wrap_untrusted(source: str, content: str) -> str:
    """Wrap outside content in <untrusted_content> tags, neutralising any copies of the tag inside it."""
    safe = _TAG.sub(r"&lt;\1", content)
    return f'<untrusted_content source="{source}">\n{safe}\n</untrusted_content>'


def check_recipient(address: str, allowed_domains: set[str]) -> str:
    """Return the normalised address if its domain is allowed, else raise PermissionError."""
    addr = address.strip().lower()
    if re.search(r"[\s,;]", addr):
        raise PermissionError(f"invalid recipient {address!r}: one plain address only")
    local, at, domain = addr.partition("@")
    if not at or not local or "@" in domain:
        raise PermissionError(f"invalid recipient {address!r}")
    if domain not in {d.lower() for d in allowed_domains}:
        raise PermissionError(f"recipient domain {domain!r} is not on the allowlist")
    return addr


def check_url(url: str, allowed_hosts: set[str]) -> str:
    """Return the URL if it's https and its host is allowed, else raise PermissionError."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or host not in {h.lower() for h in allowed_hosts}:
        raise PermissionError(f"URL {url!r} is not on the allowlist")
    return url
