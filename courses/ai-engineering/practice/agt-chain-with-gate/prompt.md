# A prompt chain with a gate

Prompt chaining splits one big task into fixed steps, with **your code** checking the output between steps. Write a two-step chain that outlines an article and then drafts it:

```python
def outline_then_draft(client, topic: str, model: str = "claude-opus-5-5") -> dict: ...
```

1. **Step 1 (outline):** call `client.messages.create(model=model, max_tokens=..., system=..., messages=[...])` with one user message that contains the topic inside tags: `<topic>{topic}</topic>`. Ask for a bullet outline where every point is a line starting with `- `. Join the reply's text blocks to get the outline.
2. **Gate:** count the outline's lines that start with `- ` (after stripping leading spaces). If there are **fewer than 3**, raise `ValueError` and **don't** make the second call. A bad outline won't become a good article, so stop early and cheaply.
3. **Step 2 (draft):** make a second call whose user message contains the outline inside `<outline>...</outline>` tags and asks for a short article that follows it.
4. Return `{"outline": outline_text, "draft": draft_text}`.

## Example

```python
outline_then_draft(client, "Why tests matter")
# call 1 reply: "- Bugs are expensive\n- Tests document intent\n- Refactor without fear"
# gate: 3 bullet lines, so continue
# call 2 reply: "Tests matter because..."
# -> {"outline": "- Bugs are expensive\n...", "draft": "Tests matter because..."}
```

**Check is free and offline.** **Run** uses the real API if your key is set.
