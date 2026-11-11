# Prompt templates as Python functions

Prompts that live in code should be built by functions, so they're consistent, testable and easy to change. Write two:

```python
def build_summary_prompt(document: str, audience: str, max_words: int) -> str: ...
def few_shot_examples(examples: list[tuple[str, str]]) -> str: ...
```

## `build_summary_prompt`

- Put the document **first**, wrapped exactly like this (tags on their own lines):

  ```
  <document>
  ...the document text...
  </document>
  ```

- **After** the document, write the instructions: summarise it for `audience` in at most `max_words` words. Include the audience text and the number in the prompt. Phrase them however you like.
- The document text must appear **only once** (inside the tags).
- Raise `ValueError` if `document` is blank or `max_words < 1`.

## `few_shot_examples`

Format `(input, output)` pairs as XML, one tag per line, joined with `"\n"`:

```python
few_shot_examples([("I love it", "positive"), ("Broke in a day", "negative")])
```

returns

```
<examples>
<example>
<input>I love it</input>
<output>positive</output>
</example>
<example>
<input>Broke in a day</input>
<output>negative</output>
</example>
</examples>
```

An empty list returns `""` (no examples, no tags).
