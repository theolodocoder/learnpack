from fake_llm import FakeAnthropic, reply, text, tool_use
from solution import chat_once


def test_returns_the_reply_text():
    client = FakeAnthropic([reply(text("Abuja."))])
    got, _ = chat_once(client, "You are terse.", [], "Capital of Nigeria?")
    assert got == "Abuja.", f"expected 'Abuja.', got {got!r}"


def test_sends_model_system_and_max_tokens():
    client = FakeAnthropic([reply(text("ok"))])
    chat_once(client, "Be kind.", [], "hi", model="claude-haiku-5-5")
    sent = client.calls[0]
    assert sent.get("model") == "claude-haiku-5-5", f"expected model 'claude-haiku-5-5', got {sent.get('model')!r}"
    assert sent.get("system") == "Be kind.", f"expected system 'Be kind.', got {sent.get('system')!r}"
    assert isinstance(sent.get("max_tokens"), int) and sent["max_tokens"] > 0, "you must send a positive max_tokens"


def test_sends_history_plus_new_message():
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
    client = FakeAnthropic([reply(text("ok"))])
    chat_once(client, "s", history, "How are you?")
    want = history + [{"role": "user", "content": "How are you?"}]
    got = client.calls[0].get("messages")
    assert got == want, f"expected messages {want!r}, got {got!r}"


def test_new_history_has_reply_and_input_is_unchanged():
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
    before = list(history)
    client = FakeAnthropic([reply(text("Fine, thanks."))])
    _, new_history = chat_once(client, "s", history, "How are you?")
    want = before + [{"role": "user", "content": "How are you?"}, {"role": "assistant", "content": "Fine, thanks."}]
    assert new_history == want, f"expected {want!r}, got {new_history!r}"
    assert history == before, "you modified the history passed in; build a new list instead"


def test_joins_text_blocks_and_skips_others():
    client = FakeAnthropic([reply(text("Hello "), tool_use("noop", {}), text("world"), stop_reason="end_turn")])
    got, _ = chat_once(client, "s", [], "hi")
    assert got == "Hello world", f"expected 'Hello world', got {got!r}"


def test_second_turn_resends_everything():
    client = FakeAnthropic([reply(text("Abuja.")), reply(text("About 4 million."))])
    _, h = chat_once(client, "s", [], "Capital of Nigeria?")
    _, h = chat_once(client, "s", h, "Population?")
    sent = client.calls[1].get("messages")
    assert len(sent) == 3, f"the second call should send 3 messages (user, assistant, user), got {len(sent or [])}"
    assert len(h) == 4, f"after two turns the history should have 4 messages, got {len(h)}"
