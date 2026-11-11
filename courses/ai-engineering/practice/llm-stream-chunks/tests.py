import contextlib
import io

from fake_llm import FakeAnthropic, reply, text
from solution import stream_chunks as _stream_chunks


def stream_chunks(*args, **kwargs):
    # Swallow the printed stream so it doesn't mix with the test report.
    with contextlib.redirect_stdout(io.StringIO()):
        return _stream_chunks(*args, **kwargs)


def test_collects_every_chunk_in_order():
    client = FakeAnthropic([reply(text("Hello there, friend!"))])
    chunks, _ = stream_chunks(client, "hi")
    want = ["Hello ", "there, ", "friend!"]
    assert chunks == want, f"expected {want!r}, got {chunks!r}"


def test_chunks_join_to_the_full_text():
    msg = "Streaming lets users read while the model is still writing."
    client = FakeAnthropic([reply(text(msg))])
    chunks, _ = stream_chunks(client, "hi")
    assert "".join(chunks) == msg, f"joined chunks should equal the full reply; got {''.join(chunks)!r}"


def test_returns_output_tokens_from_final_message():
    client = FakeAnthropic([reply(text("ok"), output_tokens=42)])
    _, out = stream_chunks(client, "hi")
    assert out == 42, f"expected 42 output tokens from get_final_message().usage, got {out!r}"


def test_sends_prompt_model_and_max_tokens():
    client = FakeAnthropic([reply(text("ok"))])
    stream_chunks(client, "Tell me a joke", model="claude-haiku-5-5")
    sent = client.calls[0]
    assert sent.get("messages") == [{"role": "user", "content": "Tell me a joke"}], f"unexpected messages: {sent.get('messages')!r}"
    assert sent.get("model") == "claude-haiku-5-5", f"expected model 'claude-haiku-5-5', got {sent.get('model')!r}"
    assert isinstance(sent.get("max_tokens"), int) and sent["max_tokens"] > 0, "send a positive max_tokens"
