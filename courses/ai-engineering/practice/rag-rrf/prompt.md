# Hybrid search with reciprocal rank fusion

You have several ranked lists of chunk ids (for example one from vector search and one from BM25). Fuse them:

```python
def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]: ...
```

- Every id in every list gets `1 / (k + rank)` from that list, where `rank` starts at **1** for the first item.
- An id's fused score is the **sum** over all the lists it appears in (lists it's missing from add nothing).
- If an id appears more than once in the same list, only its **first** (best) position counts.
- Return `(id, score)` pairs sorted by score, highest first. **Ties** are broken by id, alphabetically.
- No lists, or only empty lists, gives `[]`.

## Example

```python
vector  = ["A", "B", "C"]
keyword = ["C", "A", "D"]
reciprocal_rank_fusion([vector, keyword])
# [('A', 0.03252...), ('C', 0.03226...), ('B', 0.01612...), ('D', 0.01587...)]
#  A = 1/61 + 1/62,  C = 1/63 + 1/61,  B = 1/62,  D = 1/63
```
