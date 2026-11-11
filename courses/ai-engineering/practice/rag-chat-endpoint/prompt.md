# A `/chat` endpoint with error mapping

Build an async FastAPI endpoint that sends the user's message to Claude and maps provider failures to sensible HTTP codes.

```python
class ChatRequest(BaseModel): message: str          # 1 to 4000 characters
class ChatResponse(BaseModel): reply: str; input_tokens: int; output_tokens: int

def get_client() -> anthropic.AsyncAnthropic: ...   # given: the app-level client dependency
def llm_error_to_http(e: Exception) -> HTTPException: ...

@app.post("/chat")
async def chat(req: ChatRequest, client = Depends(get_client)) -> ChatResponse: ...
```

1. **`ChatRequest.message`** must be 1–4000 characters, so bad input gets a 422 before any API call.
2. **`chat`** awaits `client.messages.create(model=MODEL, max_tokens=1024, system=SYSTEM, messages=[{"role": "user", "content": req.message}])`. It returns the text blocks joined into `reply`, plus `response.usage.input_tokens` and `output_tokens`.
3. **`llm_error_to_http(e)`** returns (doesn't raise) an `HTTPException`:
   - `status_code` 429 or ≥ 500 → **503**, detail `"The AI service is busy. Please try again shortly."`
   - any other status code → **502**, detail `"The AI service rejected the request."`
4. In `chat`, catch exceptions that have a `status_code` (use `getattr(e, "status_code", None)`) and `raise llm_error_to_http(e)`. Exceptions **without** a `status_code` are bugs: re-raise them unchanged.

## Example

```python
app.dependency_overrides[get_client] = lambda: fake      # tests do this
client.post("/chat", json={"message": "Hi"}).json()
# {"reply": "Hello!", "input_tokens": 100, "output_tokens": 50}
# if Claude is rate-limited: status 503, {"detail": "The AI service is busy. Please try again shortly."}
```

**Check is free and offline:** tests override `get_client` with an async wrapper around the fake client, which can raise errors with `status_code` 429, 529 or 400. **Run** sends one real request if your key is set.
