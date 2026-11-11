PUNCTUATION = ".,!?;:\"'()"


def word_counts(text: str) -> dict[str, int]:
    """Count each word in `text`, ignoring case and surrounding punctuation."""
    counts: dict[str, int] = {}
    for raw in text.split():
        word = raw.lower().strip(PUNCTUATION)
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts


if __name__ == "__main__":
    print(word_counts("The cat sat. The cat ran!"))
