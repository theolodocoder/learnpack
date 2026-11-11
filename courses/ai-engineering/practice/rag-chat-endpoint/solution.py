from functools import lru_cache

import anthropic
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"
SYSTEM = "You are a concise, friendly support assistant."


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    input_tokens: int
    output_tokens: int


@lru_cache
def get_client() -> anthropic.AsyncAnthropic:
    """One shared async client for the whole app. Tests replace it with a fake."""
    return anthropic.AsyncAnthropic(timeout=60.0)


def llm_error_to_http(e: Exception) -> HTTPException:
    """429 or 5xx -> 503 (busy); any other status -> 502 (rejected)."""
    status = getattr(e, "status_code", None)
    if status == 429 or (status is not None and status >= 500):
        return HTTPException(status_code=503, detail="The AI service is busy. Please try again shortly.")
    return HTTPException(status_code=502, detail="The AI service rejected the request.")


app = FastAPI()


@app.post("/chat")
async def chat(req: ChatRequest, client=Depends(get_client)) -> ChatResponse:
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": req.message}],
        )
    except Exception as e:
        if getattr(e, "status_code", None) is None:
            raise
        raise llm_error_to_http(e) from e
    reply = "".join(b.text for b in response.content if b.type == "text")
    return ChatResponse(reply=reply, input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens)


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    try:
        r = TestClient(app).post("/chat", json={"message": "In one sentence, what is FastAPI?"})
        print(r.status_code, r.json())
    except Exception as e:  # e.g. no API key set
        print("Request failed:", type(e).__name__, e)
