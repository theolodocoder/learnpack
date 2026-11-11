# Warm-up: count words

Write a function that counts how often each word appears in a piece of text. Counting is a tiny version of what tokenizers and search indexes do all day.

```python
def word_counts(text: str) -> dict[str, int]:
```

Rules:

- Words are separated by whitespace (`text.split()` does this).
- Counting ignores case: `"The"` and `"the"` are the same word. Use the lowercase form as the key.
- Strip these punctuation characters from both ends of each word: `.,!?;:"'()`
- Skip anything that is empty after stripping (for example a lone `"!"`).
- Empty text returns `{}`.

Example:

```python
word_counts("The cat sat. The cat ran!")
# {'the': 2, 'cat': 2, 'sat': 1, 'ran': 1}
```

Press **Run** to try your function with the demo at the bottom of the file, then **Check** to run the tests.
