def stream_chunks(client, prompt: str, model: str = "claude-opus-5-5") -> tuple[list[str], int]:
    """Stream a reply, printing as it arrives; return (chunks, output_tokens)."""
    chunks: list[str] = []
    # TODO: with client.messages.stream(model=..., max_tokens=64000, messages=[...]) as stream:
    # TODO:     for each chunk in stream.text_stream: print it and append it
    # TODO:     print() once after the loop so the output ends with a newline
    # TODO:     final = stream.get_final_message()
    # TODO: return chunks and final.usage.output_tokens
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    try:
        chunks, out_tokens = stream_chunks(anthropic.Anthropic(), "Write a haiku about Lagos traffic.", model="claude-haiku-5-5")
        print(f"\n\n{len(chunks)} chunks, {out_tokens} output tokens")
    except NotImplementedError:
        print("Write stream_chunks first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
