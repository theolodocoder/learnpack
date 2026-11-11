import json
from functools import lru_cache

import anthropic
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@lru_cache
def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(timeout=60.0)


def sse_event(data: dict) -> str:
    """One SSE event: 'data: <json>' followed by a blank line."""
    # TODO
    raise NotImplementedError


async def token_events(client, message: str):
    """Yield an SSE event per text chunk, an error event on API failure, then [DONE]."""
    # TODO: try:
    # TODO:     async with client.messages.stream(...) as stream:
    # TODO:         async for chunk in stream.text_stream: yield sse_event({"text": chunk})
    # TODO: except Exception as e: re-raise if no status_code, else yield an error event
    # TODO: yield "data: [DONE]\n\n"
    yield "data: [DONE]\n\n"


app = FastAPI()


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, client=Depends(get_client)):
    # TODO: return a StreamingResponse with media_type "text/event-stream"
    return StreamingResponse(token_events(client, req.message), media_type="text/plain")


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    try:
        with TestClient(app).stream("POST", "/chat/stream", json={"message": "Count to five."}) as r:
            print(r.status_code, r.headers["content-type"])
            for line in r.iter_lines():
                if line:
                    print(line)
    except Exception as e:  # e.g. no API key set
        print("Request failed:", type(e).__name__, e)
