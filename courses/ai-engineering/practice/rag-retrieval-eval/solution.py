def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Fraction of the distinct relevant ids found in the top k retrieved."""
    wanted = set(relevant)
    if not wanted:
        return 0.0
    return len(wanted & set(retrieved[:k])) / len(wanted)


def reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float:
    """1 / rank of the first relevant id (rank from 1), or 0.0."""
    wanted = set(relevant)
    for rank, doc_id in enumerate(retrieved, start=1):
        if doc_id in wanted:
            return 1 / rank
    return 0.0


def evaluate(golden: list[dict], search, k: int = 5) -> dict:
    """Mean recall@k and MRR of search() over the golden set."""
    if not golden:
        raise ValueError("golden set is empty")
    recalls, rrs = [], []
    for item in golden:
        retrieved = search(item["question"])
        recalls.append(recall_at_k(retrieved, item["relevant"], k))
        rrs.append(reciprocal_rank(retrieved, item["relevant"]))
    return {"recall@k": sum(recalls) / len(golden), "mrr": sum(rrs) / len(golden), "n": len(golden)}


if __name__ == "__main__":
    golden = [{"question": "q1", "relevant": ["a"]}, {"question": "q2", "relevant": ["b"]}]
    results = {"q1": ["a", "x"], "q2": ["x", "b"]}
    print(evaluate(golden, lambda q: results[q], k=1))
