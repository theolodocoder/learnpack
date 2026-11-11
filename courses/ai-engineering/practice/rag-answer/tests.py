from fake_embed import embed
from fake_llm import FakeAnthropic, reply, text
from solution import NO_ANSWER, SYSTEM, VectorStore, answer, extract_citations

CHUNKS = [
    {"id": "policy.md#0", "source": "policy.md", "text": "Refunds can be requested within 30 days of purchase."},
    {"id": "policy.md#1", "source": "policy.md", "text": "Gift purchases are refunded as store credit."},
    {"id": "shipping.md#0", "source": "shipping.md", "text": "We ship to Lagos, Abuja and Accra within 5 working days."},
    {"id": "office.md#0", "source": "office.md", "text": "The office cat is called Biscuit."},
]


def make_store():
    store = VectorStore(embed)
    store.add(CHUNKS)
    return store


def test_extract_citations_filters_and_dedupes():
    got = extract_citations("30 days [policy.md#0]. Credit [policy.md#1] [made-up#9] again [policy.md#0].",
                            ["policy.md#0", "policy.md#1"])
    assert got == ["policy.md#0", "policy.md#1"], f"expected valid ids in first-seen order without repeats, got {got!r}"
    assert extract_citations("no citations here", ["a"]) == [], "no brackets means no sources"


def test_answers_with_sources():
    client = FakeAnthropic([reply(text("You have 30 days to ask [policy.md#0]."))])
    got = answer(client, "How many days do I have to request a refund?", make_store())
    want = {"answer": "You have 30 days to ask [policy.md#0].", "sources": ["policy.md#0"]}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_sends_system_and_retrieved_context():
    client = FakeAnthropic([reply(text("ok"))])
    answer(client, "How many days do I have to request a refund?", make_store(), k=2, model="claude-haiku-5-5")
    assert len(client.calls) == 1, f"expected exactly one API call, got {len(client.calls)}"
    sent = client.calls[0]
    assert sent.get("system") == SYSTEM, "pass system=SYSTEM"
    assert sent.get("model") == "claude-haiku-5-5", f"use the model argument, got {sent.get('model')!r}"
    content = sent["messages"][0]["content"]
    assert sent["messages"][0]["role"] == "user" and isinstance(content, str), "send one user message built with build_prompt"
    assert '<document id="policy.md#0" source="policy.md">' in content, "the most relevant chunk must be in the prompt"
    assert "Biscuit" not in content, "irrelevant chunks (below min_score) must not be in the prompt"
    assert content.rstrip().endswith("How many days do I have to request a refund?\n</question>"), "the question goes last"


def test_no_relevant_chunks_means_no_api_call():
    client = FakeAnthropic([])  # any call would fail
    got = answer(client, "What is the capital of Peru?", make_store())
    assert got == {"answer": NO_ANSWER, "sources": []}, f"expected the NO_ANSWER result, got {got!r}"
    assert client.calls == [], "don't call Claude when retrieval found nothing relevant"


def test_invented_sources_are_dropped():
    client = FakeAnthropic([reply(text("30 days [policy.md#0], see also [handbook.pdf#12] and [office.md#0]."))])
    got = answer(client, "How many days do I have to request a refund?", make_store())
    assert got["sources"] == ["policy.md#0"], \
        f"only ids that were retrieved for this question may be sources, got {got['sources']!r}"
