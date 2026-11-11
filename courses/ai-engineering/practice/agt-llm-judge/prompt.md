# LLM-as-judge, with a rubric and a position-bias check

Some qualities can't be checked with string matching: "is this reply polite and does it answer the question?" An LLM judge grades them against a rubric, and structured output makes its verdict machine-readable. Write:

```python
class Verdict(BaseModel):
    reasoning: str
    score: int        # 1 to 5 inclusive: use Field(ge=1, le=5)
    passed: bool

class Preference(BaseModel):
    reasoning: str
    winner: Literal["first", "second", "tie"]

def llm_judge(client, question: str, answer: str, rubric: str, model: str = "claude-opus-5-5") -> Verdict: ...
def pairwise(client, question: str, answer_a: str, answer_b: str, model: str = "claude-opus-5-5") -> str: ...
```

## `llm_judge`

Call `client.messages.parse(model=model, max_tokens=..., system=..., messages=[...], output_format=Verdict)` once and return `response.parsed_output`. The user message must contain the question, answer and rubric inside `<question>`, `<answer>` and `<rubric>` tags. In the system prompt, tell the judge to reason first, then score, and to grade **only** against the rubric.

## `pairwise`

Judges prefer whichever answer they see first more often than they should (**position bias**). Counter it by judging twice with the order swapped:

1. Call `messages.parse(..., output_format=Preference)` with `answer_a` inside `<first>` tags and `answer_b` inside `<second>` tags.
2. Call again with them swapped: `answer_b` first, `answer_a` second.
3. Map each verdict back to `"A"` or `"B"` (a `"tie"` stays `"tie"`). If both calls agree, return that (`"A"`, `"B"` or `"tie"`). If they disagree, return `"tie"`.

## Example

```python
v = llm_judge(client, "How do I reset my password?", "Click 'Forgot password'...",
              "Pass if the answer gives concrete steps and is polite.")
v.score, v.passed     # (5, True)

pairwise(client, "Explain recursion", short_answer, long_answer)
# call 1 (A first): winner "first"   -> A
# call 2 (B first): winner "second"  -> A
# -> "A"
```

**Check is free and offline.** **Run** uses the real API if your key is set.
