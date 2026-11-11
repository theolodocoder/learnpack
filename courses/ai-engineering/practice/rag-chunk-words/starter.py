def chunk_words(text: str, size: int, overlap: int) -> list[str]:
    """Windows of `size` words, each starting `size - overlap` words after the last."""
    # TODO: validate size and overlap (ValueError)
    # TODO: words = text.split(); step = size - overlap
    # TODO: for start in range(0, len(words), step): append the window; break once start + size >= len(words)
    raise NotImplementedError


if __name__ == "__main__":
    try:
        print(chunk_words("a b c d e f g h i j", size=4, overlap=1))
        print(chunk_words("a b c d e f g", size=3, overlap=0))
    except NotImplementedError:
        print("Write chunk_words, then Run again.")
