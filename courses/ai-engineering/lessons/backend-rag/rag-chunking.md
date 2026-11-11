# Chunking documents

## Why this matters

Retrieval can only return what you indexed. If you embed a whole 40-page handbook as one vector, a question about the sick-leave policy matches "the handbook" in general and you paste all 40 pages into the prompt. If you cut it into one-sentence scraps, the answer is split across pieces that each make no sense alone. **Chunking**, deciding how to split documents before embedding, is one of the biggest levers on RAG quality, and it's ordinary string processing you can get right with care.

## 1. Why chunk at all

Three reasons, in order of importance:

1. **Precision.** An embedding is a summary of its text squeezed into one vector. The longer the text, the more topics get blended together, and the less the vector looks like any one of them. A 300-word chunk about refunds matches a refund question much more sharply than a 20,000-word document that mentions refunds once.
2. **Context and cost.** You'll paste the top retrieved chunks into Claude's prompt. Five relevant 300-word chunks are about 2,000 tokens. Five whole documents might be 100,000 tokens: slower, far more expensive, and the relevant sentence is buried. Claude's context window is large, but every token you send is paid for, and long irrelevant context makes answers worse.
3. **Embedding model limits.** Embedding models have a maximum input length. Some open-source models stop at 512 tokens and silently cut off the rest.

The goal: chunks that are **small enough to be about one thing**, and **large enough to make sense on their own**.

## 2. Fixed-size chunks with overlap

The simplest method: cut every *N* words (or characters, or tokens). The problem is that cuts land in the middle of ideas, so a sentence that explains a rule gets separated from the rule. **Overlap** softens this: each chunk repeats the last few words of the previous one, so text near a boundary appears whole in at least one chunk.

```
words:     w0 w1 w2 w3 w4 w5 w6 w7 w8 w9
size=4, overlap=1  →  step = 3
chunk 0:   w0 w1 w2 w3
chunk 1:            w3 w4 w5 w6
chunk 2:                     w6 w7 w8 w9
```

```python
def chunk_words(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need size > 0 and 0 <= overlap < size")
    words = text.split()
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break  # this chunk reached the end; another would only repeat the overlap
    return chunks
```

Two details:

- `overlap < size` is required. With `overlap == size` the step is 0 and the loop never advances.
- The `break` stops a final chunk that would contain nothing but overlap.

Typical starting values: 200–500 words (roughly 250–700 tokens) with 10–20% overlap. Measure, then adjust: the *Better retrieval* lesson shows how.

Fixed-size chunking ignores the document's structure. It's a reasonable baseline for unstructured text (transcripts, scraped pages with no markup), and a fallback for pieces that are still too long after structural splitting.

## 3. Splitting on structure

Most documents have structure: headings, paragraphs, sentences, list items. Authors already grouped related ideas, so respect their groupings:

1. Split into **sections** at headings.
2. Within a section, split into **paragraphs** at blank lines.
3. **Pack** consecutive paragraphs into a chunk until adding the next would exceed your size limit.
4. A single paragraph larger than the limit is split further: by sentences, or by fixed-size windows.

This is roughly what "recursive" text splitters in RAG libraries do: try the biggest natural separator first (`"\n\n"`), then smaller ones (`"\n"`, `". "`, `" "`) only for pieces that are still too big.

Splitting Markdown into sections and paragraphs:

```python
import re

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def sections(markdown: str) -> list[tuple[str, list[str]]]:
    """[(heading, [paragraph, ...]), ...]; text before the first heading has heading ''."""
    result: list[tuple[str, list[str]]] = [("", [])]
    para: list[str] = []

    def flush():
        if para:
            result[-1][1].append(" ".join(para))
            para.clear()

    for line in markdown.splitlines():
        line = line.strip()
        if m := HEADING.match(line):
            flush()
            result.append((m.group(2).strip(), []))
        elif not line:
            flush()
        else:
            para.append(line)
    flush()
    return [(h, ps) for h, ps in result if ps]


doc = """# Refunds
Refunds are issued within 30 days.

Gift purchases get store credit.

# Shipping
We ship to Lagos, Abuja and Accra."""
print(sections(doc))
# [('Refunds', ['Refunds are issued within 30 days.', 'Gift purchases get store credit.']),
#  ('Shipping', ['We ship to Lagos, Abuja and Accra.'])]
```

`:=` (the "walrus" operator) assigns and tests in one expression. Joining a paragraph's lines with a space removes the hard line breaks many text files contain.

### Sentences

To split an oversized paragraph by sentences, a regular expression covers most English prose:

```python
import re
sentences = re.split(r"(?<=[.!?])\s+", "Refunds take 30 days. Gifts differ! Ask us?")
# ['Refunds take 30 days.', 'Gifts differ!', 'Ask us?']
```

It stumbles on abbreviations ("Dr. Okafor", "e.g. this"), so for messy text, libraries like `nltk` or `spaCy` have proper sentence splitters. For chunking, the regex is usually good enough: an occasional odd split costs little.

### Code, tables and lists

Don't split inside a fenced code block or a table row: a half-table is useless. Treat each as one unit (and if it's huge, accept a large chunk or summarise it). Keep a list together with the sentence that introduces it ("You need the following documents:").

## 4. Chunk metadata

A chunk isn't just text. Store alongside it:

- **`source`**: the file name or URL. Needed for citations ("according to *handbook.pdf*") and for deleting a document's chunks when it changes.
- **`position`**: the chunk's index within its document. Lets you fetch neighbouring chunks for extra context and show results in reading order.
- **`heading`**: the section it came from. Very useful context: "Gift purchases get store credit" means more under the heading *Refunds*.
- Others as needed: page number, author, date, language, access level (who may see it), document type.

A dataclass keeps this tidy:

```python
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    heading: str
    position: int
```

A cheap trick that often improves retrieval: **embed the heading with the text**, for example `f"{chunk.heading}\n{chunk.text}"`, while still showing only the text to users. The chunk's vector then carries its section's topic. Anthropic's *contextual retrieval* write-up takes this further, using Claude to write a sentence of document context for each chunk before embedding it.

Metadata also enables **filtering**: search only chunks where `source = 'hr-handbook.pdf'` or where the user has access. That's in *Better retrieval*.

## 5. Cleaning text

Garbage in, garbage retrieved. Before chunking, clean the extracted text:

```python
import re


def clean(text: str) -> str:
    text = text.replace(" ", " ")               # non-breaking spaces
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)     # re-join words hyphenated across lines
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)      # lines that are only a page number
    text = re.sub(r"[ \t]+", " ", text)              # runs of spaces and tabs
    text = re.sub(r"\n{3,}", "\n\n", text)           # 3+ newlines -> one blank line
    return text.strip()


print(clean("Our refund pol-\nicy lasts 30 days.\n\n\n\n12\n\nNext   section"))
# Our refund policy lasts 30 days.
#
# Next section
```

Other common clean-ups: removing repeated headers and footers ("Company Confidential - Page 3 of 40"), cookie banners and navigation menus from scraped web pages, and boilerplate like email signatures. Look at your extracted text before you index it: five minutes of reading usually reveals the junk.

> **Try it:** Paste a page of a real document into the practice editor, run it through `clean` and then `chunk_words`, and print the chunks. Do any of them make no sense on their own?

## 6. Getting text out of PDFs and other formats

Clients rarely hand you clean Markdown. Mostly it's PDFs, Word files and web pages. Extraction is its own problem:

- **PDFs** store positioned glyphs, not paragraphs. Libraries reconstruct the text: **pypdf** (pure Python, simple), **PyMuPDF** (`pymupdf`, fast and good with layout), **pdfplumber** (good for tables). Multi-column layouts, headers and footers, and tables are where they struggle.
- **Scanned PDFs** are images: there's no text to extract. You need OCR (Tesseract), or a vision-capable model. Claude can read PDF pages directly as documents, which is excellent for small volumes and pricey for thousands of pages.
- **Word / HTML / slides:** `python-docx`, `BeautifulSoup`, `python-pptx`. Tools such as `unstructured` and `docling` wrap many formats behind one interface and return elements (title, paragraph, table) you can chunk on.

A minimal pypdf extraction, for reference:

```python
from pypdf import PdfReader  # pip install pypdf

reader = PdfReader("handbook.pdf")
pages = [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
# keep the page number as chunk metadata, so citations can say "page 12"
```

Whatever the tool, the pipeline is the same: **extract → clean → split on structure → attach metadata → embed**.

## 7. Choosing a chunk size

There's no universal best size, but there are good defaults and a method:

- Start with **structure-aware chunks of about 200–400 words** with a little overlap (or none, when splitting on paragraphs).
- **Smaller chunks** give more precise matches but less context per chunk; questions about specific facts (dates, prices, names) like them.
- **Larger chunks** carry more context; broad "explain how X works" questions like them.
- A middle path: retrieve small chunks for precision, then send the model the surrounding section (the neighbours by `position`). This is often called "small-to-big" retrieval.

Then **measure**: build a small set of questions with known answers and compare chunking settings by how often the right chunk is retrieved. *Better retrieval* teaches exactly that.

## Common mistakes

- **Not chunking** (whole documents as one vector) or **chunking too small** (single sentences that mean nothing alone).
- **Overlap ≥ size**, which loops forever or produces only duplicates.
- **Throwing away metadata.** Without `source` you can't cite; without `position` you can't fetch neighbours or re-order.
- **Indexing junk**: page numbers, headers, navigation menus, hyphenated fragments. Read your extracted text.
- **Splitting through code blocks and tables.**
- **Changing chunking without re-indexing everything.** Old and new chunks mixed in one index give confusing results.
- **Assuming PDF extraction worked.** Spot-check pages; scanned PDFs often come back empty.

## Recap

- Chunk so each piece is about one thing yet makes sense alone; that sharpens retrieval and cuts prompt cost.
- Fixed-size windows with overlap are a simple baseline (`step = size - overlap`, and stop once a chunk reaches the end).
- Structure-aware splitting (headings → paragraphs → sentences, packing up to a size limit) usually works better.
- Attach metadata (source, position, heading, page) to every chunk; consider embedding the heading with the text.
- Clean extracted text first; PDF extraction needs tools like pypdf or PyMuPDF, and OCR or a vision model for scans.
- Start around 200–400 words, then measure and adjust.
