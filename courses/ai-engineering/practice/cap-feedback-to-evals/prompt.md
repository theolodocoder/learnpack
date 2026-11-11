# Turn user feedback into eval cases

Every thumbs-down from a real user is a free test case, if you capture it. Your product logs each answer with the user's rating and, when a reviewer (you, or the business owner) has fixed a bad answer, a correction:

```python
{"id": 17, "question": "Do you deliver to Ibadan?", "answer": "No.",
 "rating": "down", "correction": "Yes, Ibadan delivery takes 2 days and costs ₦3,500."}
```

`rating` is `"up"`, `"down"` or `None`; `correction` may be missing, `None` or blank.

Write:

```python
def feedback_to_evals(logs: list[dict]) -> list[dict]:
def needs_review(logs: list[dict]) -> list[int]:
```

## `feedback_to_evals`

Build eval cases, in log order:

- `rating == "down"` **with** a non-blank correction → `{"id": "fb-<id>", "input": question, "expected": correction (stripped), "source": "thumbs_down"}`. These are bugs you fixed; the eval keeps them fixed.
- `rating == "up"` → `{"id": "fb-<id>", "input": question, "expected": answer, "source": "thumbs_up"}`. These are regression cases: answers that were good and must stay good.
- Everything else (no rating, or a thumbs-down with no correction yet) → no case.
- **No duplicate questions.** Two questions are the same if they match after lowercasing, stripping and collapsing runs of whitespace to one space. Keep only the first case for each question.

## `needs_review`

Return the ids of thumbs-down logs that have no usable correction yet, in log order: your review queue.

## Example

```python
logs = [
    {"id": 1, "question": "Do you deliver to Ibadan?", "answer": "No.", "rating": "down",
     "correction": "Yes, in 2 days for ₦3,500."},
    {"id": 2, "question": "Opening hours?", "answer": "9am to 6pm, Monday to Saturday.", "rating": "up"},
    {"id": 3, "question": "do you  deliver to ibadan? ", "answer": "No.", "rating": "up"},
    {"id": 4, "question": "Can I pay on delivery?", "answer": "Yes.", "rating": "down", "correction": None},
    {"id": 5, "question": "Any discounts?", "answer": "Not now.", "rating": None},
]
feedback_to_evals(logs)
# [{'id': 'fb-1', 'input': 'Do you deliver to Ibadan?', 'expected': 'Yes, in 2 days for ₦3,500.', 'source': 'thumbs_down'},
#  {'id': 'fb-2', 'input': 'Opening hours?', 'expected': '9am to 6pm, Monday to Saturday.', 'source': 'thumbs_up'}]
needs_review(logs)   # [4]
```
