"""Fetch a web page for the in-app browser panel.

Pages that allow framing are shown live in the panel. Pages that refuse (X-Frame-Options or
CSP frame-ancestors) are fetched here and shown as a reading copy: their HTML and styles,
without scripts, with links resolved against the original address.
server.py exposes browse() as GET /api/browse, behind the same host and token checks as the rest of the API.
"""
import ipaddress
import re
import socket
import urllib.error
import urllib.request
from html import escape, unescape
from urllib.parse import urlsplit

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
MAX_BYTES = 5_000_000


class BrowseError(Exception):
    """A page can't be shown; the message is written for the learner."""


def check_url(url: str) -> None:
    """Allow only public http(s) addresses, so the fetcher can't be pointed at the local network."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise BrowseError("Only web links (http or https) can open here.")
    try:
        infos = socket.getaddrinfo(parts.hostname, None)
    except socket.gaierror:
        raise BrowseError(f"Couldn't reach {parts.hostname}. Check your internet connection.")
    # Check every address the name resolves to, so a public name pointing at 127.0.0.1 is caught too.
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise BrowseError("Addresses on your own computer or network can't be opened here.")


def frame_allowed(headers) -> bool:
    """Would a browser let this page load inside our panel?"""
    if headers.get("X-Frame-Options"):
        return False
    match = re.search(r"frame-ancestors([^;]*)", headers.get("Content-Security-Policy", ""), re.I)
    return "*" in match.group(1).split() if match else True


def readable(html: str, base_url: str) -> str:
    """The page without scripts, with a <base> so its links, styles and images still resolve."""
    # Scripts, inline on* handlers and javascript: links are removed so the copy can't run code in our page.
    html = re.sub(r"(?is)<script\b.*?</script\s*>", "", html)
    html = re.sub(r"(?is)</?noscript\b[^>]*>", "", html)  # show no-JS fallbacks, since scripts won't run
    html = re.sub(r"""(?i)\son[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", "", html)
    html = re.sub(r"""(?i)(href|src)\s*=\s*(["'])\s*javascript:[^"']*\2""", r"\1=\2#\2", html)
    base = f'<base href="{escape(base_url, quote=True)}">'
    if re.search(r"(?i)<head\b[^>]*>", html):
        return re.sub(r"(?i)(<head\b[^>]*>)", lambda m: m.group(1) + base, html, count=1)
    return base + html


def browse(url: str) -> dict:
    """{url, title, embeddable, html}. html is set only when the page must be shown as a reading copy."""
    check_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            final_url = resp.geturl()
            check_url(final_url)  # redirects are followed, so check where we ended up too
            if frame_allowed(resp.headers):
                return {"url": final_url, "title": "", "embeddable": True, "html": None}
            if resp.headers.get_content_type() != "text/html":
                raise BrowseError("This file can't be shown inside the course.")
            text = resp.read(MAX_BYTES).decode(resp.headers.get_content_charset() or "utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise BrowseError(f"The site answered with an error ({e.code}).")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if isinstance(e, BrowseError):  # BrowseError from check_url above; let it through unchanged
            raise
        raise BrowseError("Couldn't load the page. Check your internet connection.")
    title = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
    return {"url": final_url, "title": unescape(title.group(1).strip()) if title else "",
            "embeddable": False, "html": readable(text, final_url)}
