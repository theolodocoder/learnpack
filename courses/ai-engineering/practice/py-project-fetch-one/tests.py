import asyncio

import httpx

from solution import Failure, Post, fetch_one

GOOD = {"id": 1, "userId": 7, "title": "Hello", "body": "First post"}


def _fetch(handler, url="/posts/1"):
    async def go():
        async with httpx.AsyncClient(base_url="https://api.example.com",
                                     transport=httpx.MockTransport(handler)) as client:
            return await fetch_one(client, url)

    return asyncio.run(go())


def test_valid_response_becomes_post():
    got = _fetch(lambda r: httpx.Response(200, json=GOOD))
    assert isinstance(got, Post), f"expected a Post, got {got!r}"
    assert (got.id, got.user_id, got.title) == (1, 7, "Hello"), f"got {got!r}"


def test_http_error_becomes_failure_with_status():
    got = _fetch(lambda r: httpx.Response(404), url="/posts/99")
    assert isinstance(got, Failure), f"expected a Failure, got {got!r}"
    assert got.url == "/posts/99" and got.error == "HTTP 404", f"expected url '/posts/99', error 'HTTP 404', got {got!r}"


def test_network_error_becomes_failure():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    got = _fetch(handler)
    assert isinstance(got, Failure), f"expected a Failure, got {got!r}"
    assert got.error == "request failed: ConnectError", f"expected 'request failed: ConnectError', got {got.error!r}"


def test_non_json_body_becomes_failure():
    got = _fetch(lambda r: httpx.Response(200, text="<html>oops</html>"))
    assert isinstance(got, Failure) and got.error == "invalid JSON", f"expected Failure 'invalid JSON', got {got!r}"


def test_wrong_shape_becomes_invalid_data_failure():
    bad = {"id": 0, "userId": 7, "title": "", "body": "x"}
    got = _fetch(lambda r: httpx.Response(200, json=bad))
    assert isinstance(got, Failure), f"id 0 and an empty title should fail validation, got {got!r}"
    assert got.error.startswith("invalid data"), f"expected the error to start with 'invalid data', got {got.error!r}"
