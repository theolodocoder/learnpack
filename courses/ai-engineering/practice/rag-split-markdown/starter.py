import re
from dataclasses import dataclass

HEADING = re.compile(r"^#{1,6}\s+(.*)$")


@dataclass
class Chunk:
    text: str
    source: str
    heading: str
    position: int


def split_markdown(text: str, source: str, max_words: int = 200) -> list[Chunk]:
    """Chunks that follow headings and paragraphs, packed up to max_words."""
    # Suggested plan:
    # 1. Walk the lines, building sections: a list of (heading, [paragraph, ...]).
    #    A heading line starts a new section; a blank line ends the current paragraph.
    # 2. For each section, pack paragraphs into chunks of at most max_words words
    #    (an oversized paragraph is a chunk on its own).
    # 3. Number the chunks with position 0, 1, 2, ...
    raise NotImplementedError


if __name__ == "__main__":
    doc = """# Refunds
Refunds are issued
within 30 days.

Gift purchases get store credit.

## Shipping
We ship to Lagos, Abuja and Accra."""
    try:
        for chunk in split_markdown(doc, "policy.md", max_words=8):
            print(chunk)
    except NotImplementedError:
        print("Write split_markdown, then Run again.")
