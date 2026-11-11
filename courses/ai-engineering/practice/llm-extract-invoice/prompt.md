# Extract an invoice into a Pydantic model

Use `client.messages.parse` to turn messy invoice text into a validated `Invoice` object.

The models are already written in the starter:

```python
class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float

class Invoice(BaseModel):
    vendor: str
    invoice_number: str
    currency: str            # ISO code such as "NGN", "USD"
    total: float
    due_date: str | None     # "YYYY-MM-DD", or None if the invoice doesn't say
    line_items: list[LineItem]
```

Write:

```python
def extract_invoice(client, text: str, model: str = "claude-opus-5-5") -> Invoice: ...
```

1. Call `client.messages.parse(model=..., max_tokens=16000, messages=[...], output_format=Invoice)`.
2. The single user message should give a short instruction and the invoice text wrapped as `<invoice>\n{text}\n</invoice>`.
3. Return `response.parsed_output` (already an `Invoice`).

You may add `Field(description=...)` to the models if you like; keep the field names and types.

## Example

```python
inv = extract_invoice(client, "ACME Ltd  INV-0042\n2 x Widget @ 1,500 NGN\nTotal: NGN 3,000\nDue 2026-12-01")
inv.vendor         # "ACME Ltd"
inv.total          # 3000.0
inv.line_items[0]  # LineItem(description='Widget', quantity=2, unit_price=1500.0)
```

**Check is free and offline:** the fake client returns scripted JSON and validates it against your `output_format`. **Run** uses the real API if your key is set.
