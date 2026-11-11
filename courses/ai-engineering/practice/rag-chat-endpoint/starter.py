from functools import lru_cache

import anthropic
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"
SYSTEM = "You are a concise, friendly support assistant."


class ChatRequest(BaseModel):
    message: str  # TODO: 1 to 4000 characters


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
    # TODO
    raise NotImplementedError


app = FastAPI()


@app.post("/chat")
async def chat(req: ChatRequest, client=Depends(get_client)) -> ChatResponse:
    # TODO: try: response = await client.messages.create(...)
    # TODO: except Exception as e: re-raise if it has no status_code, else raise llm_error_to_http(e)
    # TODO: join the text blocks and return a ChatResponse with the token counts
    raise HTTPException(status_code=501, detail="Not implemented yet")


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    try:
        r = TestClient(app).post("/chat", json={"message": "In one sentence, what is FastAPI?"})
        print(r.status_code, r.json())
    except Exception as e:  # e.g. no API key set
        print("Request failed:", type(e).__name__, e)
