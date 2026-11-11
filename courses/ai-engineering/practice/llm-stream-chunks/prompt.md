# Collect a streamed reply

Write:

```python
def stream_chunks(client, prompt: str, model: str = "claude-opus-5-5") -> tuple[list[str], int]: ...
```

1. Open a stream with `client.messages.stream(model=..., max_tokens=64000, messages=[{"role": "user", "content": prompt}])` as a context manager (`with ... as stream:`).
2. Loop over `stream.text_stream`, printing each chunk as it arrives (`print(chunk, end="", flush=True)`) **and** appending it to a list.
3. After the loop, `print()` once so the output ends with a newline. Then, still inside the `with`, call `stream.get_final_message()` to get the complete response.
4. Return `(chunks, final.usage.output_tokens)`.

## Example

```python
chunks, out_tokens = stream_chunks(client, "Say hello in three words")
# prints:  Hello there, friend!
# chunks     == ["Hello ", "there, ", "friend!"]   (the exact split depends on the model)
# out_tokens == 6
```

**Check is free and offline:** the tests use a fake client that streams a scripted reply word by word. **Run** uses the real API if your key is set.
