from solution import chunk_words


def test_overlapping_windows():
    got = chunk_words("a b c d e f g h i j", size=4, overlap=1)
    want = ["a b c d", "d e f g", "g h i j"]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_no_overlap_keeps_short_last_chunk():
    got = chunk_words("a b c d e f g", size=3, overlap=0)
    want = ["a b c", "d e f", "g"]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_no_chunk_that_only_repeats_overlap():
    got = chunk_words("a b c d e f", size=4, overlap=2)
    want = ["a b c d", "c d e f"]
    assert got == want, f"stop once a chunk reaches the end: expected {want!r}, got {got!r}"


def test_short_and_empty_text():
    assert chunk_words("one two", size=5, overlap=2) == ["one two"], "text shorter than size is one chunk"
    assert chunk_words("", size=5, overlap=1) == [], "empty text gives []"
    assert chunk_words("   \n  ", size=5, overlap=1) == [], "whitespace-only text gives []"


def test_normalises_whitespace():
    got = chunk_words("Refunds  are\nissued\twithin 30 days.", size=3, overlap=1)
    want = ["Refunds are issued", "issued within 30", "30 days."]
    assert got == want, f"split on any whitespace and join with single spaces: expected {want!r}, got {got!r}"


def test_invalid_arguments_raise():
    for size, overlap in [(0, 0), (-1, 0), (3, 3), (3, 5), (3, -1)]:
        try:
            chunk_words("a b c d", size=size, overlap=overlap)
        except ValueError:
            continue
        raise AssertionError(f"size={size}, overlap={overlap} should raise ValueError")
