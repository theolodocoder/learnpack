import re
from dataclasses import dataclass

HEADING = re.compile(r"^#{1,6}\s+(.*)$")


@dataclass
class Chunk:
    text: str
    source: str
    heading: str
    position: int


def _sections(text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = [("", [])]
    para: list[str] = []

    def flush():
        if para:
            sections[-1][1].append(" ".join(para))
            para.clear()

    for line in text.splitlines():
        line = line.strip()
        if m := HEADING.match(line):
            flush()
            sections.append((m.group(1).strip(), []))
        elif not line:
            flush()
        else:
            para.append(line)
    flush()
    return sections


def split_markdown(text: str, source: str, max_words: int = 200) -> list[Chunk]:
    """Chunks that follow headings and paragraphs, packed up to max_words."""
    chunks: list[Chunk] = []
    for heading, paragraphs in _sections(text):
        current: list[str] = []
        words = 0
        for p in paragraphs:
            n = len(p.split())
            if current and words + n > max_words:
                chunks.append(Chunk("\n\n".join(current), source, heading, len(chunks)))
                current, words = [], 0
            current.append(p)
            words += n
        if current:
            chunks.append(Chunk("\n\n".join(current), source, heading, len(chunks)))
    return chunks


if __name__ == "__main__":
    doc = """# Refunds
Refunds are issued
within 30 days.

Gift purchases get store credit.

## Shipping
We ship to Lagos, Abuja and Accra."""
    for chunk in split_markdown(doc, "policy.md", max_words=8):
        print(chunk)
