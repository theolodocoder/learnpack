def normalise(question: str) -> str:
    """Lowercase, strip, and collapse runs of whitespace to one space."""
    # TODO
    return question


def feedback_to_evals(logs: list[dict]) -> list[dict]:
    """Eval cases from thumbs-down-with-correction and thumbs-up logs, first per question, in order."""
    cases: list[dict] = []
    # TODO
    return cases


def needs_review(logs: list[dict]) -> list[int]:
    """Ids of thumbs-down logs with no usable correction yet."""
    # TODO
    return []


if __name__ == "__main__":
    logs = [
        {"id": 1, "question": "Do you deliver to Ibadan?", "answer": "No.", "rating": "down",
         "correction": "Yes, in 2 days for ₦3,500."},
        {"id": 2, "question": "Opening hours?", "answer": "9am to 6pm, Monday to Saturday.", "rating": "up"},
        {"id": 3, "question": "do you  deliver to ibadan? ", "answer": "No.", "rating": "up"},
        {"id": 4, "question": "Can I pay on delivery?", "answer": "Yes.", "rating": "down", "correction": None},
        {"id": 5, "question": "Any discounts?", "answer": "Not now.", "rating": None},
    ]
    for case in feedback_to_evals(logs):
        print(case)
    print(needs_review(logs))
