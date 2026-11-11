# Answer questions with citations (or say "I don't know")

Connect the pieces into the query side of RAG. The starter already contains a working `VectorStore`, `build_prompt`, `SYSTEM` and `NO_ANSWER`. Write:

```python
def extract_citations(text: str, valid_ids: list[str]) -> list[str]: ...
def answer(client, question: str, store, k: int = 3, min_score: float = 0.3,
           model: str = "claude-opus-5-5") -> dict: ...
```

**`extract_citations`** finds every `[something]` in `text` (regex `\[([^\[\]]+)\]`) and returns the ones that are in `valid_ids`, in order of first appearance, without duplicates. Ids the model made up are dropped.

**`answer`**:

1. `hits = store.search(question, k=k, min_score=min_score)`.
2. If there are no hits, return `{"answer": NO_ANSWER, "sources": []}` **without calling the client**.
3. Otherwise call `client.messages.create(model=model, max_tokens=1024, system=SYSTEM, messages=[{"role": "user", "content": build_prompt(question, chunks)}])`, where `chunks` are the hit chunks in ranked order.
4. Join the response's text blocks into the answer, and return `{"answer": text, "sources": extract_citations(text, ids_of_the_retrieved_chunks)}`.

## Example

```python
store = VectorStore(embed)
store.add([{"id": "policy.md#0", "source": "policy.md", "text": "Refunds can be requested within 30 days of purchase."}, ...])

answer(client, "How many days do I have to request a refund?", store)
# {"answer": "You have 30 days [policy.md#0].", "sources": ["policy.md#0"]}

answer(client, "What is the capital of Peru?", store)
# {"answer": "I don't know based on the provided documents.", "sources": []}   (no API call)
```

**Check is free and offline:** tests use `FakeAnthropic` and `fake_embed`. **Run** asks the real Claude one question about a tiny built-in document set if your key is set.
