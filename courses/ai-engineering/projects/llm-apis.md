# Project 1: Document extractor

Build a command-line tool that turns messy documents (invoices, CVs, receipts) into clean, validated JSON. It handles one file or a whole folder, processes batches concurrently without tripping rate limits, retries transient failures, and finishes with a cost report.

This is one of the most common paid AI gigs: "we have thousands of PDFs/emails/forms and need the data in a spreadsheet or database." Freelance marketplaces and agencies post variations of it every week (invoice processing for accountants, CV parsing for recruiters, contract summaries for law firms). A polished, tested version in your portfolio is direct evidence you can do that job.

Build it in **its own GitHub repository**, then paste the repo URL (and a demo URL if you deploy the stretch API) into the fields below.

## Requirements

1. **Input:** a path to a `.txt` file, or a folder of them. (PDF input is a stretch goal.)
2. **Document types:** at least two, each with its own Pydantic model. Suggested:
   - `Invoice`: vendor, invoice number, currency, total, due date (optional), line items.
   - `CV`: name, email (optional), phone (optional), skills (list), work history (list of role, company, start, end).
3. **Extraction** uses `client.messages.parse(..., output_format=Model)`, with the document text wrapped in XML tags and a clear prompt per document type.
4. **Validation:** Pydantic validates every result. Add at least one business rule (for invoices: line items add up to the total, within a small tolerance). Documents that fail validation are reported, not silently dropped.
5. **Batch mode** uses `anthropic.AsyncAnthropic` and `asyncio.gather`, with an `asyncio.Semaphore` limiting concurrent requests (configurable, default 5).
6. **Retries:** retry 429 and 5xx errors with exponential backoff and jitter; don't retry 400s. Set `max_retries=0` on the client so retries aren't doubled.
7. **Output:** one JSON file per input document (in an `out/` folder), plus a summary `results.jsonl` or CSV.
8. **Cost report** at the end: number of documents, successes, failures, total input/output tokens, total cost in dollars, and average cost per document.
9. **Tests** that run offline with a fake client: no API key needed for `pytest`.
10. **README** with setup, usage examples, a sample of the output, and measured cost per document.

## Suggested file layout

```
doc-extractor/
├── .env.example            # ANTHROPIC_API_KEY=
├── .gitignore              # .env, out/, __pycache__/
├── README.md
├── pyproject.toml          # or requirements.txt
├── extractor/
│   ├── __init__.py
│   ├── models.py           # Invoice, CV, LineItem ... (Pydantic)
│   ├── prompts.py          # prompt-building functions, one per document type
│   ├── extract.py          # extract_one(client, text, doc_type) -> model
│   ├── batch.py            # extract_many(client, paths, concurrency) with a semaphore
│   ├── retry.py            # with_retry(...) and is_retryable(...)
│   ├── cost.py             # PRICES, CostTracker
│   └── cli.py              # argparse entry point
├── samples/                # a few anonymised example documents
└── tests/
    ├── fake_client.py
    ├── test_models.py
    ├── test_extract.py
    ├── test_batch.py
    └── test_retry.py
```

Keep it this simple. No framework, no database: files in, files out.

## Build plan

### Step 1: models and prompts (no API yet)

Write the Pydantic models with `Field(description=...)` on anything ambiguous, `X | None` for data that may be missing, and `Literal` for closed sets (e.g. currency codes you support). Write `build_invoice_prompt(text)` and `build_cv_prompt(text)`. Unit-test both: valid data parses, invalid data raises, the document is inside its tags.

### Step 2: extract one document

```python
async def extract_one(client, text: str, model_cls: type[BaseModel], prompt: str,
                      model: str = "claude-haiku-5-5") -> tuple[BaseModel, object]:
    response = await client.messages.parse(
        model=model, max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
        output_format=model_cls,
    )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise ExtractionError(f"stopped with {response.stop_reason}")
    return response.parsed_output, response.usage
```

Run it on a sample file with your real key. Start with Haiku while developing; compare against Opus on your samples once it works and note the difference in your README.

### Step 3: business-rule validation

Add a check that line items add up to the total. Decide what happens on failure: mark the document as "needs review" in the output rather than discarding it.

### Step 4: retries

Write an async `with_retry(fn, max_retries=3, base_delay=1.0, sleep=asyncio.sleep)` that awaits `fn()` and retries on `status_code` 429 or ≥ 500 with `base · 2ⁿ + jitter`. Inject `sleep` so tests don't wait.

### Step 5: batch mode

```python
async def extract_many(client, paths, concurrency: int = 5):
    sem = asyncio.Semaphore(concurrency)

    async def worker(path):
        async with sem:
            try:
                return path, await with_retry(lambda: extract_one(client, ...)), None
            except Exception as e:
                return path, None, e

    return await asyncio.gather(*(worker(p) for p in paths))
```

Each worker catches its own exception, so one bad document can't sink the batch. Time a batch of 20 documents with `concurrency=1` and `concurrency=5` and put both numbers in the README.

### Step 6: cost report and CLI

Record every response's `usage` in a `CostTracker`, then print a report:

```
Processed 20 documents in 14.2 s
  succeeded: 18   needs review: 1   failed: 1
  tokens: 41,230 in / 9,870 out
  cost: $0.0091 total, $0.00046 per document (claude-haiku-5-5)
```

Wire it up with `argparse`: `python -m extractor.cli samples/ --type invoice --model claude-haiku-5-5 --concurrency 5`.

### Step 7: README and polish

Explain what it does, how to run it, what the output looks like, accuracy notes from your samples, and cost per document. Screenshots or a short terminal recording help.

## Testing with a fake client

Your tests must not need an API key. Write a tiny async fake that mimics `messages.parse`:

```python
# tests/fake_client.py
import json
from types import SimpleNamespace


class FakeAsyncAnthropic:
    def __init__(self, script):
        self.script = list(script)   # JSON strings to return, or exceptions to raise
        self.calls = []
        self.messages = self

    async def parse(self, *, output_format, **kwargs):
        self.calls.append({**kwargs, "output_format": output_format})
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return SimpleNamespace(
            stop_reason="end_turn",
            parsed_output=output_format.model_validate(json.loads(item)),
            usage=SimpleNamespace(input_tokens=1000, output_tokens=200),
        )


class RateLimited(Exception):
    status_code = 429
```

Then test the behaviour that matters:

- `extract_one` sends the document inside its tags and the right `output_format`.
- A 429 followed by success returns the result and records one retry (pass `sleep=` a function that appends to a list).
- A 400 isn't retried.
- With `concurrency=2` and 6 documents, no more than 2 calls are ever in flight (track a counter in the fake with a small `await asyncio.sleep(0.01)`).
- One failing document in a batch doesn't stop the others.
- The cost report adds up: 3 documents × known usage = the expected dollar amount.

Use `asyncio.run(...)` inside plain test functions, or `pytest-asyncio` if you prefer.

## Stretch goals

- **PDF input.** Claude reads PDFs directly through a `document` content block, including scanned pages and tables:

  ```python
  import base64
  from pathlib import Path

  pdf_data = base64.standard_b64encode(Path("invoice.pdf").read_bytes()).decode()
  messages = [{
      "role": "user",
      "content": [
          {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data}},
          {"type": "text", "text": "Extract the invoice details from this document."},
      ],
  }]
  ```

  Use `count_tokens` on a few PDFs first: pages cost more tokens than plain text.

- **A FastAPI endpoint.** `POST /extract?type=invoice` accepting an uploaded file and returning the validated JSON, with the same retries and cost logging. Deploy it and paste the URL below.
- **Confidence and review queue.** Add a `confidence: Literal["high", "medium", "low"]` field and a list of `uncertain_fields`, and write low-confidence results to a separate review file.
- **Accuracy evaluation.** Hand-label 10 documents and write a script that reports per-field accuracy for each model, so you can justify your model choice with numbers.
- **Message Batches API.** For large overnight jobs, compare cost and turnaround using Anthropic's batch processing (it's discounted for non-urgent work).
