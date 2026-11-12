import pytest

from engine.browse import BrowseError, check_url, frame_allowed, readable


def test_frame_allowed_reads_both_headers():
    assert frame_allowed({}) is True
    assert frame_allowed({"X-Frame-Options": "DENY"}) is False
    assert frame_allowed({"Content-Security-Policy": "default-src 'self'; frame-ancestors 'self'"}) is False
    assert frame_allowed({"Content-Security-Policy": "frame-ancestors *"}) is True
    assert frame_allowed({"Content-Security-Policy": "default-src 'self'"}) is True


def test_readable_strips_scripts_and_handlers_and_adds_base():
    html = ('<html><head><title>T</title><script>alert(1)</script></head>'
            '<body onload="evil()"><a href="javascript:evil()">x</a><noscript><p>No JS</p></noscript>'
            '<a href="/docs">docs</a></body></html>')
    out = readable(html, "https://example.com/a/b")
    assert "<script" not in out and "onload" not in out and "javascript:" not in out
    assert '<base href="https://example.com/a/b">' in out and "<p>No JS</p>" in out and 'href="/docs"' in out


def test_readable_without_head():
    assert readable("<p>hi</p>", "https://e.com/").startswith('<base href="https://e.com/">')


@pytest.mark.parametrize("url", ["ftp://example.com/x", "file:///etc/passwd", "http://localhost:8000/", "http://127.0.0.1/", "http://192.168.1.1/"])
def test_check_url_blocks_non_web_and_local(url):
    with pytest.raises(BrowseError):
        check_url(url)
