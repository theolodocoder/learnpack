import json
from collections.abc import Iterator

import httpx


def stream_answer(client: httpx.Client, question: str) -> Iterator[str]:
    """POST the question to /chat/stream and yield text chunks from the SSE events.

    Stops at [DONE]; raises RuntimeError on an error event and httpx.HTTPStatusError on a non-2xx status.
    """
    # TODO: with client.stream("POST", "/chat/stream", json=...) as response:
    # TODO:     response.raise_for_status()
    # TODO:     for line in response.iter_lines(): ...
    yield from ()


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        body = b'data: {"text": "Hello "}\n\ndata: {"text": "there"}\n\ndata: [DONE]\n\n'
        return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

    client = httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))
    for chunk in stream_answer(client, "Hi"):
        print(repr(chunk))
