import json
from collections.abc import Iterator

import httpx


def stream_answer(client: httpx.Client, question: str) -> Iterator[str]:
    """POST the question to /chat/stream and yield text chunks from the SSE events.

    Stops at [DONE]; raises RuntimeError on an error event and httpx.HTTPStatusError on a non-2xx status.
    """
    with client.stream("POST", "/chat/stream", json={"message": question}) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            data = line.removeprefix("data: ")
            if data == "[DONE]":
                return
            event = json.loads(data)
            if "error" in event:
                raise RuntimeError(event["error"])
            if "text" in event:
                yield event["text"]


if __name__ == "__main__":
    def handler(request: httpx.Request) -> httpx.Response:
        body = b'data: {"text": "Hello "}\n\ndata: {"text": "there"}\n\ndata: [DONE]\n\n'
        return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

    client = httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))
    print("".join(stream_answer(client, "Hi")))
