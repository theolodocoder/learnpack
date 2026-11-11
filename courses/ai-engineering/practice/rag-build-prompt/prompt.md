# Build the RAG prompt

Write the function that turns retrieved chunks and a question into the user message for Claude:

```python
def build_prompt(question: str, chunks: list[dict]) -> str: ...
```

Each chunk is a dict with `"id"`, `"source"` and `"text"`. Produce exactly this layout (lines joined with `"\n"`, no trailing newline):

```
<documents>
<document id="policy.md#0" source="policy.md">
Refunds can be requested within 30 days of purchase.
</document>
<document id="policy.md#1" source="policy.md">
Gift purchases are refunded as store credit.
</document>
</documents>

<question>
How many days do I have to request a refund?
</question>
```

- Documents appear in the order given, each as an opening tag with `id` and `source`, the text on its own line(s), and a closing tag.
- One blank line between `</documents>` and `<question>`.
- With no chunks, the documents block is just `<documents>` and `</documents>` on consecutive lines.
- Strip leading and trailing whitespace from the question and from each chunk's text.
- **Safety:** a chunk's text must not be able to close its tag early. Replace any `</document>` or `</documents>` inside chunk text with `[/document]` / `[/documents]`.

The starter also contains a `SYSTEM` prompt for you to read: it tells Claude to answer only from the documents, cite ids in square brackets, and say "I don't know" otherwise.
