from solution import Chunk, split_markdown

DOC = """# Refunds
Refunds are issued
within 30 days.

Gift purchases get store credit.

## Shipping
We ship to Lagos, Abuja and Accra."""


def test_splits_on_headings_and_paragraphs():
    got = split_markdown(DOC, "policy.md", max_words=8)
    want = [
        Chunk("Refunds are issued within 30 days.", "policy.md", "Refunds", 0),
        Chunk("Gift purchases get store credit.", "policy.md", "Refunds", 1),
        Chunk("We ship to Lagos, Abuja and Accra.", "policy.md", "Shipping", 2),
    ]
    assert got == want, f"expected {want!r}\n got {got!r}"


def test_packs_paragraphs_up_to_max_words():
    got = split_markdown(DOC, "policy.md", max_words=20)
    texts = [c.text for c in got]
    want = ["Refunds are issued within 30 days.\n\nGift purchases get store credit.", "We ship to Lagos, Abuja and Accra."]
    assert texts == want, f"paragraphs in one section should share a chunk while <= max_words; got {texts!r}"
    assert [c.position for c in got] == [0, 1], "positions should be 0, 1, ..."


def test_chunks_never_cross_headings():
    got = split_markdown(DOC, "policy.md", max_words=1000)
    assert [c.heading for c in got] == ["Refunds", "Shipping"], f"one chunk per section expected, got {got!r}"


def test_text_before_first_heading_and_oversized_paragraph():
    doc = "Intro line one\nintro line two.\n\n" + " ".join(["word"] * 12) + "\n\n# Next\nShort."
    got = split_markdown(doc, "a.md", max_words=5)
    want = [
        Chunk("Intro line one intro line two.", "a.md", "", 0),
        Chunk(" ".join(["word"] * 12), "a.md", "", 1),
        Chunk("Short.", "a.md", "Next", 2),
    ]
    assert got == want, f"expected {want!r}\n got {got!r}"


def test_empty_and_heading_only_docs():
    assert split_markdown("", "x.md") == [], "empty text gives []"
    assert split_markdown("# Title\n\n## Sub\n", "x.md") == [], "headings without paragraphs give no chunks"
