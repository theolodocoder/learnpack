def stream_chunks(client, prompt: str, model: str = "claude-opus-5-5") -> tuple[list[str], int]:
    """Stream a reply, printing as it arrives; return (chunks, output_tokens)."""
    chunks: list[str] = []
    with client.messages.stream(
        model=model, max_tokens=64000, messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        print()  # finish the line
        final = stream.get_final_message()
    return chunks, final.usage.output_tokens
