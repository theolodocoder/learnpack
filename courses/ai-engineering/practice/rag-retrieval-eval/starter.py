def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Fraction of the distinct relevant ids found in the top k retrieved."""
    # TODO
    raise NotImplementedError


def reciprocal_rank(retrieved: list[str], relevant: list[str]) -> float:
    """1 / rank of the first relevant id (rank from 1), or 0.0."""
    # TODO
    raise NotImplementedError


def evaluate(golden: list[dict], search, k: int = 5) -> dict:
    """Mean recall@k and MRR of search() over the golden set."""
    # TODO: ValueError for an empty golden set
    # TODO: for each item: retrieved = search(item["question"]); collect both metrics
    # TODO: return {"recall@k": ..., "mrr": ..., "n": len(golden)}
    raise NotImplementedError


if __name__ == "__main__":
    golden = [{"question": "q1", "relevant": ["a"]}, {"question": "q2", "relevant": ["b"]}]
    results = {"q1": ["a", "x"], "q2": ["x", "b"]}
    try:
        print(evaluate(golden, lambda q: results[q], k=1))
    except NotImplementedError:
        print("Write the three functions, then Run again.")
