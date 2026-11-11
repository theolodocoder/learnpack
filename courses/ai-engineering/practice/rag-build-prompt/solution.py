SYSTEM = (
    "You answer questions using only the documents provided in <documents>. "
    "After each claim, cite the id of the document it came from in square brackets, like [policy.md#2]. "
    "If the documents do not contain the answer, say \"I don't know\" and nothing else. "
    "Do not use outside knowledge."
)


def _safe(text: str) -> str:
    return text.strip().replace("</documents>", "[/documents]").replace("</document>", "[/document]")


def build_prompt(question: str, chunks: list[dict]) -> str:
    """The user message: retrieved chunks in <document> tags, then the question."""
    lines = ["<documents>"]
    for c in chunks:
        lines.append(f'<document id="{c["id"]}" source="{c["source"]}">')
        lines.append(_safe(c["text"]))
        lines.append("</document>")
    lines += ["</documents>", "", "<question>", question.strip(), "</question>"]
    return "\n".join(lines)


if __name__ == "__main__":
    chunks = [
        {"id": "policy.md#0", "source": "policy.md", "text": "Refunds can be requested within 30 days of purchase."},
        {"id": "policy.md#1", "source": "policy.md", "text": "Gift purchases are refunded as store credit."},
    ]
    print(build_prompt("How many days do I have to request a refund?", chunks))
