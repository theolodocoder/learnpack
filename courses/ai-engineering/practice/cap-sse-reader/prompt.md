# Read your backend's stream from a frontend

Your FastAPI backend streams answers as server-sent events from `POST /chat/stream`:

```
data: {"text": "Hello "}

data: {"text": "there"}

data: [DONE]

```

If Claude fails mid-stream, the backend sends `data: {"error": "..."}` and then `data: [DONE]`.

A Streamlit frontend shows a stream with `st.write_stream(some_generator)`, so all it needs is a Python generator of text chunks. Write that generator:

```python
def stream_answer(client: httpx.Client, question: str) -> Iterator[str]:
```

1. Send `POST /chat/stream` with JSON body `{"message": question}`, using `client.stream(...)` so you read the response as it arrives (the client already has a `base_url`).
2. If the status is not 2xx, raise `httpx.HTTPStatusError` (`response.raise_for_status()` does this).
3. Go through the body line by line (`response.iter_lines()`). Ignore blank lines and lines that don't start with `data: `.
4. For each `data: ` line:
   - `[DONE]` → stop.
   - JSON with a `"text"` key → `yield` the text.
   - JSON with an `"error"` key → raise `RuntimeError(the error message)`.

## Example

```python
def handler(request):
    body = b'data: {"text": "Hello "}\n\ndata: {"text": "there"}\n\ndata: [DONE]\n\n'
    return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

client = httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(handler))
"".join(stream_answer(client, "Hi"))   # 'Hello there'
```

The tests use `httpx.MockTransport`, so nothing goes over the network.
