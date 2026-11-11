import re

import numpy as np

NO_ANSWER = "I don't know based on the provided documents."

SYSTEM = (
    "You answer questions using only the documents provided in <documents>. "
    "After each claim, cite the id of the document it came from in square brackets, like [policy.md#2]. "
    "If the documents do not contain the answer, say \"I don't know\" and nothing else. "
    "Do not use outside knowledge."
)


def normalise(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


class VectorStore:
    """In-memory store: chunks plus a matrix of normalised embeddings."""

    def __init__(self, embed):
        self.embed = embed
        self.chunks: list[dict] = []
        self.vectors: np.ndarray | None = None

    def add(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        vecs = normalise(np.asarray(self.embed([c["text"] for c in chunks]), dtype=float))
        self.vectors = vecs if self.vectors is None else np.vstack([self.vectors, vecs])
        self.chunks.extend(chunks)

    def search(self, query: str, k: int = 3, min_score: float | None = None) -> list[tuple[dict, float]]:
        if self.vectors is None or k <= 0:
            return []
        q = normalise(np.asarray(self.embed([query]), dtype=float))[0]
        scores = self.vectors @ q
        hits = []
        for i in np.argsort(-scores, kind="stable")[:k]:
            if min_score is not None and scores[i] < min_score:
                break
            hits.append((self.chunks[i], float(scores[i])))
        return hits


def build_prompt(question: str, chunks: list[dict]) -> str:
    lines = ["<documents>"]
    for c in chunks:
        text = c["text"].strip().replace("</documents>", "[/documents]").replace("</document>", "[/document]")
        lines += [f'<document id="{c["id"]}" source="{c["source"]}">', text, "</document>"]
    lines += ["</documents>", "", "<question>", question.strip(), "</question>"]
    return "\n".join(lines)


def extract_citations(text: str, valid_ids: list[str]) -> list[str]:
    """Ids cited as [id] in text that are in valid_ids, first-seen order, no duplicates."""
    found: list[str] = []
    for cited in re.findall(r"\[([^\[\]]+)\]", text):
        if cited in valid_ids and cited not in found:
            found.append(cited)
    return found


def answer(client, question: str, store, k: int = 3, min_score: float = 0.3,
           model: str = "claude-opus-5-5") -> dict:
    """Retrieve, then answer with citations; NO_ANSWER without an API call if nothing is relevant."""
    hits = store.search(question, k=k, min_score=min_score)
    if not hits:
        return {"answer": NO_ANSWER, "sources": []}
    chunks = [chunk for chunk, _ in hits]
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_prompt(question, chunks)}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    return {"answer": text, "sources": extract_citations(text, [c["id"] for c in chunks])}


if __name__ == "__main__":
    import anthropic
    from fake_embed import embed

    store = VectorStore(embed)
    store.add([
        {"id": "policy.md#0", "source": "policy.md", "text": "Refunds can be requested within 30 days of purchase."},
        {"id": "policy.md#1", "source": "policy.md", "text": "Gift purchases are refunded as store credit."},
        {"id": "shipping.md#0", "source": "shipping.md", "text": "We ship to Lagos, Abuja and Accra within 5 working days."},
    ])
    try:
        print(answer(None, "What is the capital of Peru?", store))  # no hits, so no client needed
        print(answer(anthropic.Anthropic(), "How many days do I have to request a refund?", store,
                     model="claude-haiku-5-5"))
    except NotImplementedError:
        print("Write extract_citations and answer, then Run again.")
    except Exception as e:  # e.g. no API key set
        print("API call failed (is ANTHROPIC_API_KEY set?):", type(e).__name__, e)
