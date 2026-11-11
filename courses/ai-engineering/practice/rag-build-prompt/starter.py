SYSTEM = (
    "You answer questions using only the documents provided in <documents>. "
    "After each claim, cite the id of the document it came from in square brackets, like [policy.md#2]. "
    "If the documents do not contain the answer, say \"I don't know\" and nothing else. "
    "Do not use outside knowledge."
)


def build_prompt(question: str, chunks: list[dict]) -> str:
    """The user message: retrieved chunks in <document> tags, then the question."""
    # TODO: lines = ["<documents>"]
    # TODO: for each chunk: opening tag with id and source, the (stripped, made-safe) text, closing tag
    # TODO: "</documents>", "", "<question>", the stripped question, "</question>"
    # TODO: return "\n".join(lines)
    raise NotImplementedError


if __name__ == "__main__":
    chunks = [
        {"id": "policy.md#0", "source": "policy.md", "text": "Refunds can be requested within 30 days of purchase."},
        {"id": "policy.md#1", "source": "policy.md", "text": "Gift purchases are refunded as store credit."},
    ]
    try:
        print(build_prompt("How many days do I have to request a refund?", chunks))
    except NotImplementedError:
        print("Write build_prompt, then Run again.")
