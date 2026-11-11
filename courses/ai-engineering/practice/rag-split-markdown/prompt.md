# Structure-aware chunks with metadata

Split a Markdown document into chunks that follow its headings and paragraphs, and attach metadata to each.

```python
@dataclass
class Chunk:
    text: str
    source: str
    heading: str
    position: int

def split_markdown(text: str, source: str, max_words: int = 200) -> list[Chunk]: ...
```

Rules:

1. **Headings** are lines (after stripping spaces) matching `^#{1,6}\s+(.*)$`. A heading starts a new section; its text (without the `#`s) becomes `heading` for the chunks in that section. Text before the first heading has `heading=""`. Heading lines are not part of any chunk's text.
2. **Paragraphs** are runs of non-blank lines separated by blank lines. A paragraph's lines are stripped and joined with a single space.
3. **Packing:** within a section, add paragraphs to the current chunk while its total word count (`len(text.split())`) stays `<= max_words`. When the next paragraph would push it over, start a new chunk. A single paragraph longer than `max_words` becomes a chunk on its own (don't split it). Paragraphs in one chunk are joined with `"\n\n"`. Chunks never cross a heading.
4. `source` is copied onto every chunk; `position` numbers chunks 0, 1, 2, ... across the whole document.
5. Empty text, or headings with no paragraphs, produce no chunks.

## Example

```python
doc = """# Refunds
Refunds are issued
within 30 days.

Gift purchases get store credit.

## Shipping
We ship to Lagos, Abuja and Accra."""

split_markdown(doc, "policy.md", max_words=8)
# [Chunk(text='Refunds are issued within 30 days.', source='policy.md', heading='Refunds', position=0),
#  Chunk(text='Gift purchases get store credit.', source='policy.md', heading='Refunds', position=1),
#  Chunk(text='We ship to Lagos, Abuja and Accra.', source='policy.md', heading='Shipping', position=2)]
```

With `max_words=20`, the two Refunds paragraphs (6 + 5 words) would share one chunk: `'Refunds are issued within 30 days.\n\nGift purchases get store credit.'`.
