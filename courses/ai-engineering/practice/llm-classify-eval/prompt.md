# Classify, then measure your prompt

A prompt is only "good" if it works on real inputs. Build a sentiment classifier and a tiny evaluation loop for it.

```python
LABELS = ("positive", "negative", "neutral")

def classify_sentiment(client, review: str, model: str = "claude-opus-5-5") -> str: ...
def evaluate(client, cases: list[tuple[str, str]], model: str = "claude-opus-5-5") -> float: ...
```

## `classify_sentiment`

1. Send a `system` prompt that explains the task and names **all three labels**, and asks for the answer inside `<label>...</label>` tags.
2. Send one user message whose content contains the review wrapped in tags: `<review>\n{review}\n</review>`.
3. Find the text between `<label>` and `</label>` in the reply (the reply may contain other text too), strip it and lowercase it.
4. Return that label if it's one of `LABELS`, otherwise return `"unknown"` (also when there are no tags).

## `evaluate`

Run `classify_sentiment` on each `(review, expected_label)` pair and return the fraction it got right, as a float between 0 and 1. An empty list returns `0.0`.

## Example

```python
classify_sentiment(client, "Arrived fast and works perfectly.")
# reply text: "<label>Positive</label>"  ->  "positive"

evaluate(client, [("Great!", "positive"), ("Awful.", "negative"), ("It's a phone.", "neutral")])
# 0.6666666666666666   if one of the three came back wrong
```

**Check is free and offline.** **Run** uses the real API if your key is set (Haiku is plenty for this).
