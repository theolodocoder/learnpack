# Fixed-size chunks with overlap

Write:

```python
def chunk_words(text: str, size: int, overlap: int) -> list[str]: ...
```

Split `text` into words with `text.split()`, then return windows of `size` words, each joined with single spaces. Each window starts `size - overlap` words after the previous one, so neighbouring chunks share `overlap` words.

- Stop as soon as a chunk reaches the end of the text: don't emit a final chunk that only repeats words already covered.
- Empty or whitespace-only text returns `[]`.
- Raise `ValueError` if `size <= 0`, `overlap < 0`, or `overlap >= size` (the window would never move forward).

## Example

```python
chunk_words("a b c d e f g h i j", size=4, overlap=1)
# ['a b c d', 'd e f g', 'g h i j']

chunk_words("a b c d e f g", size=3, overlap=0)
# ['a b c', 'd e f', 'g']

chunk_words("one two", size=5, overlap=2)
# ['one two']
```
