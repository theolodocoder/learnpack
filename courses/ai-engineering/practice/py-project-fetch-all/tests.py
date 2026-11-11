import asyncio
import json
import tempfile
from pathlib import Path

import httpx

from solution import Failure, Post, fetch_all, write_report


class FakeAPI:
    """Async mock handler: /posts/N returns post N, except the ids in `missing` (404) and `broken` (bad data)."""

    def __init__(self, missing=(), broken=(), delay=0.02):
        self.missing, self.broken, self.delay = set(missing), set(broken), delay
        self.active = 0
        self.peak = 0

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            await asyncio.sleep(self.delay)
            n = int(request.url.path.rsplit("/", 1)[-1])
            if n in self.missing:
                return httpx.Response(404)
            if n in self.broken:
                return httpx.Response(200, json={"id": n, "title": ""})
            return httpx.Response(200, json={"id": n, "userId": 1, "title": f"Post {n}", "body": "b"})
        finally:
            self.active -= 1


def _run(api, urls, limit):
    async def go():
        async with httpx.AsyncClient(base_url="https://api.example.com",
                                     transport=httpx.MockTransport(api)) as client:
            return await fetch_all(client, urls, limit=limit)

    return asyncio.run(go())


def test_fetches_all_posts_in_url_order():
    posts, failures = _run(FakeAPI(), [f"/posts/{n}" for n in (3, 1, 2)], limit=3)
    assert failures == [], f"expected no failures, got {failures!r}"
    ids = [p.id for p in posts]
    assert ids == [3, 1, 2], f"expected posts in URL order [3, 1, 2], got {ids!r}"


def test_collects_failures_without_crashing():
    api = FakeAPI(missing={2}, broken={4})
    posts, failures = _run(api, [f"/posts/{n}" for n in range(1, 6)], limit=5)
    assert [p.id for p in posts] == [1, 3, 5], f"expected posts 1, 3, 5, got {[p.id for p in posts]!r}"
    assert [f.url for f in failures] == ["/posts/2", "/posts/4"], f"got failures {failures!r}"
    assert failures[0].error == "HTTP 404", f"expected 'HTTP 404', got {failures[0].error!r}"
    assert failures[1].error.startswith("invalid data"), f"expected 'invalid data...', got {failures[1].error!r}"


def test_respects_the_concurrency_limit():
    api = FakeAPI()
    _run(api, [f"/posts/{n}" for n in range(1, 11)], limit=3)
    assert api.peak <= 3, f"{api.peak} requests were in flight at once, but limit was 3"
    assert api.peak == 3, f"expected requests to overlap up to the limit of 3, saw at most {api.peak}"


def test_write_report_saves_posts_and_failures_as_json():
    posts = [Post.model_validate({"id": 1, "userId": 2, "title": "T", "body": "B"})]
    failures = [Failure(url="/posts/9", error="HTTP 404")]
    path = Path(tempfile.mkdtemp()) / "nested" / "report.json"
    write_report(posts, failures, path)
    assert path.exists(), f"{path} was not created (did you create the parent folder?)"
    got = json.loads(path.read_text())
    want = {"posts": [{"id": 1, "user_id": 2, "title": "T", "body": "B"}],
            "failures": [{"url": "/posts/9", "error": "HTTP 404"}]}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_empty_url_list():
    posts, failures = _run(FakeAPI(), [], limit=2)
    assert posts == [] and failures == [], f"expected ([], []), got ({posts!r}, {failures!r})"
