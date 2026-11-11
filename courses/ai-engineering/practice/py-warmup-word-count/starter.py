PUNCTUATION = ".,!?;:\"'()"


def word_counts(text: str) -> dict[str, int]:
    """Count each word in `text`, ignoring case and surrounding punctuation."""
    counts: dict[str, int] = {}
    # TODO: loop over text.split()
    # TODO: lowercase each word and strip PUNCTUATION from both ends
    # TODO: skip empty words, then add 1 to counts[word]
    return counts


if __name__ == "__main__":
    print(word_counts("The cat sat. The cat ran!"))
