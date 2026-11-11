from fake_llm import FakeAnthropic, reply, text
from solution import ROUTES, route


def test_routes_billing_to_billing_prompt():
    client = FakeAnthropic([reply(text("<category>billing</category>")), reply(text("Sorry about that."))])
    got = route(client, "I was charged twice")
    assert got == ("billing", "Sorry about that."), f"expected ('billing', 'Sorry about that.'), got {got!r}"
    second = client.calls[1]
    assert second.get("system") == ROUTES["billing"], "call 2 should use ROUTES['billing'] as its system prompt"
    assert second["messages"] == [{"role": "user", "content": "I was charged twice"}], \
        f"call 2 should send just the customer's message, got {second['messages']!r}"


def test_router_uses_the_cheap_model_and_tags():
    client = FakeAnthropic([reply(text("<category>technical</category>")), reply(text("Step 1..."))])
    route(client, "App crashes on upload")
    first = client.calls[0]
    assert first.get("model") == "claude-haiku-5-5", f"classify with router_model, got {first.get('model')!r}"
    assert client.calls[1].get("model") == "claude-opus-5-5", "answer with `model`"
    content = str(first["messages"][-1]["content"])
    assert "<message>" in content and "App crashes on upload" in content, "wrap the message in <message> tags"


def test_category_is_case_and_space_insensitive():
    client = FakeAnthropic([reply(text("Sure. <category> Technical \n</category>")), reply(text("ok"))])
    category, _ = route(client, "Error 500")
    assert category == "technical", f"expected 'technical', got {category!r}"


def test_unknown_category_falls_back_to_general():
    client = FakeAnthropic([reply(text("<category>legal</category>")), reply(text("ok"))])
    category, _ = route(client, "Can I sue you?")
    assert category == "general", f"an unknown category should become 'general', got {category!r}"
    assert client.calls[1].get("system") == ROUTES["general"], "use the general prompt for the fallback"


def test_missing_tags_fall_back_to_general():
    client = FakeAnthropic([reply(text("billing probably")), reply(text("ok"))])
    category, _ = route(client, "Hmm")
    assert category == "general", f"no <category> tags should give 'general', got {category!r}"
