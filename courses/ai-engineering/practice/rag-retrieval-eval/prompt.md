# Measure retrieval: recall@k and MRR

Write the metrics you'll use to compare retrieval settings, and a function that runs them over a golden set:

```python
def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float: ...
def reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float: ...
def evaluate(golden: list[dict], search, k: int = 5) -> dict: ...
```

1. **`recall_at_k`**: the fraction of the (distinct) `relevant` ids that appear in the first `k` of `retrieved`. If `relevant` is empty, return `0.0`.
2. **`reciprocal_rank`**: `1 / rank` of the first retrieved id that is relevant (rank starts at 1), or `0.0` if none is.
3. **`evaluate`**: `golden` is a list of `{"question": str, "relevant": [ids]}`. `search(question)` returns a ranked list of ids. Call `search` once per question and return
   `{"recall@k": mean recall_at_k, "mrr": mean reciprocal_rank, "n": number of questions}` (the key is literally `"recall@k"`). An empty `golden` raises `ValueError`.

## Example

```python
recall_at_k(["a", "x", "b"], ["a", "b", "c"], k=2)   # 0.333...  (only "a" is in the top 2)
reciprocal_rank(["x", "y", "a"], ["a"])               # 0.333...  (first hit at rank 3)

golden = [{"question": "q1", "relevant": ["a"]}, {"question": "q2", "relevant": ["b"]}]
results = {"q1": ["a", "x"], "q2": ["x", "b"]}
evaluate(golden, lambda q: results[q], k=1)
# {"recall@k": 0.5, "mrr": 0.75, "n": 2}
```
