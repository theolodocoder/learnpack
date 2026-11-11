# Stream Claude's answer as server-sent events

Build a streaming endpoint that forwards Claude's text to the browser as server-sent events (SSE).

```python
def sse_event(data: dict) -> str: ...
async def token_events(client, message: str): ...      # an async generator of SSE strings

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, client = Depends(get_client)): ...
```

1. **`sse_event(data)`** returns `"data: " + json.dumps(data) + "\n\n"`.
2. **`token_events(client, message)`** is an async generator:
   - `async with client.messages.stream(model=MODEL, max_tokens=1024, messages=[{"role": "user", "content": message}]) as stream:`
   - for every chunk in `stream.text_stream` (use `async for`), yield `sse_event({"text": chunk})`;
   - if an exception **with a `status_code`** is raised anywhere in that, yield `sse_event({"error": "The AI service failed. Please try again."})` instead of crashing (exceptions without one are bugs: re-raise them);
   - always finish by yielding `"data: [DONE]\n\n"`.
3. **`chat_stream`** returns `StreamingResponse(token_events(client, req.message), media_type="text/event-stream")`.

## Example

```python
r = client.post("/chat/stream", json={"message": "Hi"})
r.headers["content-type"]   # "text/event-stream; charset=utf-8"
r.text
# 'data: {"text": "Hello "}\n\ndata: {"text": "there"}\n\ndata: [DONE]\n\n'
```

Why an error *event*? Once the first chunk is sent, the response status (200) is already on its way. The only way to tell the browser something went wrong is inside the stream.

**Check is free and offline:** tests swap `get_client` for an async wrapper around the fake client. **Run** streams one real answer if your key is set.
