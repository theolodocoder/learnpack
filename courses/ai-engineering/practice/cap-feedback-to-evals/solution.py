def normalise(question: str) -> str:
    """Lowercase, strip, and collapse runs of whitespace to one space."""
    return " ".join(question.lower().split())


def _correction(log: dict) -> str:
    return (log.get("correction") or "").strip()


def feedback_to_evals(logs: list[dict]) -> list[dict]:
    """Eval cases from thumbs-down-with-correction and thumbs-up logs, first per question, in order."""
    cases, seen = [], set()
    for log in logs:
        if log.get("rating") == "down" and _correction(log):
            expected, source = _correction(log), "thumbs_down"
        elif log.get("rating") == "up":
            expected, source = log["answer"], "thumbs_up"
        else:
            continue
        key = normalise(log["question"])
        if key in seen:
            continue
        seen.add(key)
        cases.append({"id": f"fb-{log['id']}", "input": log["question"], "expected": expected, "source": source})
    return cases


def needs_review(logs: list[dict]) -> list[int]:
    """Ids of thumbs-down logs with no usable correction yet."""
    return [log["id"] for log in logs if log.get("rating") == "down" and not _correction(log)]
