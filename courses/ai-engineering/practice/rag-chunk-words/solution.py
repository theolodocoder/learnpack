def chunk_words(text: str, size: int, overlap: int) -> list[str]:
    """Windows of `size` words, each starting `size - overlap` words after the last."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("need size > 0 and 0 <= overlap < size")
    words = text.split()
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks


if __name__ == "__main__":
    print(chunk_words("a b c d e f g h i j", size=4, overlap=1))
    print(chunk_words("a b c d e f g", size=3, overlap=0))
