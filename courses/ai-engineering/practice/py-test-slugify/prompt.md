# Write tests that catch bugs

This time you write the **tests**, not the code. The file already contains a working `slugify` function (it turns titles into URL-friendly slugs). Your job is to write test functions that would catch it if someone broke it.

The rules `slugify` follows:

1. The result is lowercase.
2. Every run of characters that are not `a`–`z` or `0`–`9` (spaces, punctuation, symbols) becomes a **single** `-`.
3. There is no `-` at the start or end.

```python
slugify("Hello, World!")        # 'hello-world'
slugify("  RAG -- 101  ")       # 'rag-101'
slugify("")                     # ''
```

Write **at least 3** functions named `test_...` in the same file, using plain `assert`, pytest style (no classes, no imports needed). Call `slugify` directly in them.

**How Check grades you:** it runs your tests against the correct `slugify` (they must all pass), then against four broken versions. Each broken version must make **at least one** of your tests fail. The broken versions:

- one that forgets to lowercase,
- one that turns each bad character into its own `-` instead of collapsing runs (`"a  b"` → `"a--b"`),
- one that leaves `-` at the start or end,
- one that only replaces whitespace and keeps punctuation (`"hi!"` → `"hi!"`).

Think "arrange, act, assert": pick an input that exposes each rule, call `slugify`, compare to the exact expected string.

Press **Run** to run your tests yourself: the demo block calls every `test_` function and reports which fail.
