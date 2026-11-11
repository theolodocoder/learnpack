def stream_text(client, prompt: str, system: str = "", model: str = "claude-opus-5-5"):
    """Yield the reply's text chunks as they arrive."""
    # TODO: build the kwargs; only include system if it's non-empty
    # TODO: with client.messages.stream(**kwargs) as stream:
    # TODO:     yield each chunk from stream.text_stream
    raise NotImplementedError
    yield  # keeps this a generator function until you write the real body


if __name__ == "__main__":
    import anthropic

    try:
        for chunk in stream_text(anthropic.Anthropic(), "Count to five in Yoruba.", model="claude-haiku-5-5"):
            print(chunk, end="", flush=True)
        print()
    except NotImplementedError:
        print("Write stream_text first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
