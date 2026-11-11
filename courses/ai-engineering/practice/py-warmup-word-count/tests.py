from solution import word_counts


def test_counts_simple_words():
    got = word_counts("a b a")
    want = {"a": 2, "b": 1}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_ignores_case():
    got = word_counts("Python python PYTHON")
    want = {"python": 3}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_strips_punctuation():
    got = word_counts("The cat sat. The cat ran!")
    want = {"the": 2, "cat": 2, "sat": 1, "ran": 1}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_skips_words_that_are_only_punctuation():
    got = word_counts('hello ! "world" ?')
    want = {"hello": 1, "world": 1}
    assert got == want, f"expected {want!r}, got {got!r}"


def test_empty_text_gives_empty_dict():
    got = word_counts("")
    assert got == {}, f"expected {{}}, got {got!r}"
