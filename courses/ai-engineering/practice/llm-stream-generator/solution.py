def stream_text(client, prompt: str, system: str = "", model: str = "claude-opus-5-5"):
    """Yield the reply's text chunks as they arrive."""
    kwargs = {"model": model, "max_tokens": 64000, "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    with client.messages.stream(**kwargs) as stream:
        yield from stream.text_stream
