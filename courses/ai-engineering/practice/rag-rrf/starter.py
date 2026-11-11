def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse ranked lists of ids: score(id) = sum of 1 / (k + rank), rank starting at 1."""
    # TODO: scores: dict[str, float] = {}
    # TODO: for each list: for rank, id in enumerate(list, start=1): add 1/(k+rank) the first time you see id in this list
    # TODO: sort by (-score, id)
    raise NotImplementedError


if __name__ == "__main__":
    try:
        for doc_id, score in reciprocal_rank_fusion([["A", "B", "C"], ["C", "A", "D"]]):
            print(doc_id, round(score, 5))
    except NotImplementedError:
        print("Write reciprocal_rank_fusion, then Run again.")
