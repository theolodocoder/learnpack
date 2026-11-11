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
    return f"data: {json.dumps(data)}\n\n"


async def token_events(client, message: str):
    """Yield an SSE event per text chunk, an error event on API failure, then [DONE]."""
    try:
        async with client.messages.stream(
            model=MODEL, max_tokens=1024, messages=[{"role": "user", "content": message}],
        ) as stream:
            async for chunk in stream.text_stream:
                yield sse_event({"text": chunk})
    except Exception as e:
        if getattr(e, "status_code", None) is None:
            raise
        yield sse_event({"error": "The AI service failed. Please try again."})
    yield "data: [DONE]\n\n"


app = FastAPI()


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, client=Depends(get_client)):
    return StreamingResponse(token_events(client, req.message), media_type="text/event-stream")


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
