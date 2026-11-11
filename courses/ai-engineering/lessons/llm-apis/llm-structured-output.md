# Structured output with Pydantic

## Why this matters

Most paid LLM work isn't chat. It's turning messy text (invoices, CVs, emails, contracts, support tickets) into data a program can use: rows in a database, fields in a CRM, a decision in a workflow. Programs need **exact structure**: a field called `total` that is a number, every time. Free-form text breaks that contract in a hundred small ways. Structured output makes the model's reply conform to a schema you define, and Pydantic turns it into a typed, validated Python object. This is the single most useful technique in this section.

## 1. Why free text breaks programs

Ask for an invoice total in plain text and you might get any of these, from the same prompt on different runs:

```
The total is ₦3,500.
Total: 3500 NGN
Sure! Here's the total amount due on this invoice: NGN 3,500.00
```

You could write a regex for each pattern, but tomorrow's reply will use a new one. Asking for JSON in the prompt helps, but not always:

~~~
Here is the JSON you requested:
```json
{"total": "3,500", "currency": "NGN"}
```
~~~

Now there's a preamble, a code fence, and `total` is a string with a comma. `json.loads` fails, or succeeds with the wrong type and your database insert fails later. In production these failures are rare but constant, and they always happen at 2 a.m.

**Structured output** solves this at the source: you send a JSON schema with the request, and the API constrains generation so the reply is valid JSON matching that schema. No preamble, no fences, the right types.

## 2. The easy path: `messages.parse` with a Pydantic model

You already know Pydantic from the Python refresher. Define the shape you want, then pass the class as `output_format`:

```python
import anthropic
from pydantic import BaseModel

client = anthropic.Anthropic()


class Contact(BaseModel):
    name: str
    email: str
    company: str | None
    wants_demo: bool


email_text = """Hi, this is Ngozi Eze from Kudi Logistics (ngozi@kudi.ng).
We'd love to see a demo of your routing product next week."""

response = client.messages.parse(
    model="claude-opus-5-5",
    max_tokens=16000,
    messages=[{"role": "user", "content": f"Extract the contact details.\n\n<email>\n{email_text}\n</email>"}],
    output_format=Contact,
)

contact = response.parsed_output
print(type(contact).__name__)  # Contact
print(contact.name, contact.email, contact.wants_demo)
# Ngozi Eze ngozi@kudi.ng True
```

What happens:

1. The SDK converts `Contact` into a JSON schema and sends it with the request.
2. The model generates JSON that matches the schema.
3. The SDK validates the reply with Pydantic and puts the resulting `Contact` object in `response.parsed_output`.

You get autocompletion, type checking, and a guarantee that `contact.wants_demo` is a `bool`. The rest of the response is still there: `response.usage`, `response.stop_reason`, and `response.content` (whose text block holds the raw JSON).

Nested models and lists work as you'd expect:

```python
class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float


class Invoice(BaseModel):
    vendor: str
    invoice_number: str
    currency: str
    total: float
    due_date: str | None
    line_items: list[LineItem]
```

## 3. The raw path: `output_config` with a JSON schema

`messages.parse` is a convenience. Underneath, it uses the `output_config` parameter of `messages.create`, which you can also use directly when you don't have (or want) a Pydantic model, for example when the schema comes from a config file or another language's codebase:

```python
import json

schema = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["billing", "bug", "feature", "other"]},
        "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string"},
    },
    "required": ["category", "urgency", "summary"],
    "additionalProperties": False,
}

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1000,
    messages=[{"role": "user", "content": "Ticket: I was charged twice this month!!"}],
    output_config={"format": {"type": "json_schema", "schema": schema}},
)

raw = "".join(b.text for b in response.content if b.type == "text")
data = json.loads(raw)
print(data)
# {'category': 'billing', 'urgency': 'high', 'summary': 'Customer was charged twice this month.'}
```

Two rules for hand-written schemas:

- **`"additionalProperties": False`** on every object, so the model can't invent extra keys.
- **`"required"`** lists every property. To make a field optional, keep it required but allow `null`: `{"type": ["string", "null"]}`. (That's what Pydantic generates for `str | None`.)

You can still validate the raw JSON with Pydantic:

```python
from typing import Literal
from pydantic import BaseModel

class Ticket(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
    urgency: Literal["low", "medium", "high"]
    summary: str

ticket = Ticket.model_validate_json(raw)
```

You can generate the schema from a model too, with `Ticket.model_json_schema()`, though `messages.parse` already does this for you (and cleans up the parts the API doesn't support).

> **Note:** Use one or the other on a single call: `output_format=` with `messages.parse`, or `output_config={"format": ...}` with `messages.create`. Passing both raises an error. `output_config` can carry other settings too, such as `effort`, alongside `format`.

## 4. Validate, and handle failures

Structured output makes invalid JSON very rare, but "valid JSON" isn't the same as "correct data", and a few failure modes remain:

1. **`stop_reason == "max_tokens"`**: the JSON was cut off. Raise `max_tokens` (long lists of line items need room).
2. **`stop_reason == "refusal"`**: the model declined; there's no usable output.
3. **Validation fails** on something the schema can't express (see section 5), so Pydantic raises `ValidationError`.
4. **The values are wrong**: valid shape, but the model misread the total or invented a due date.

Handle the first three in code:

```python
from pydantic import ValidationError


def extract_contact(client, text: str) -> Contact | None:
    for attempt in range(2):
        try:
            response = client.messages.parse(
                model="claude-opus-5-5", max_tokens=4000,
                messages=[{"role": "user", "content": f"Extract the contact.\n\n<email>\n{text}\n</email>"}],
                output_format=Contact,
            )
        except ValidationError as e:
            print(f"attempt {attempt + 1}: invalid output: {e.error_count()} errors")
            continue
        if response.stop_reason != "end_turn" or response.parsed_output is None:
            print(f"attempt {attempt + 1}: stopped with {response.stop_reason}")
            continue
        return response.parsed_output
    return None
```

Retrying once is reasonable, since output varies between calls. Retrying forever isn't: if two attempts fail, the input is probably the problem. Return `None` (or raise a clear error) and let the caller log it for a human to look at.

For the fourth failure, **business-rule checks** catch a lot:

```python
from pydantic import model_validator

class CheckedInvoice(Invoice):
    @model_validator(mode="after")
    def totals_add_up(self):
        computed = sum(i.quantity * i.unit_price for i in self.line_items)
        if self.line_items and abs(computed - self.total) > 0.01:
            raise ValueError(f"line items sum to {computed}, but total is {self.total}")
        return self
```

Validate **after** extraction with `CheckedInvoice.model_validate(invoice.model_dump())` and flag failures for review, rather than putting cross-field rules into the schema you send.

## 5. Designing good schemas

The schema is part of your prompt: field names, types and descriptions all tell the model what you want. Good schemas get better extractions.

**Use enums for closed sets.** If the category can only be one of four values, say so with `Literal` (or `"enum"`). Free-text categories come back as "Billing", "billing issue", "payments"… and your analytics breaks.

```python
from typing import Literal

class Ticket(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
```

Always include a catch-all like `"other"` so the model isn't forced to pick a wrong label.

**Make fields optional when the data might be missing.** If a CV may not list a phone number, use `phone: str | None`. A required `str` *forces* the model to produce something, and it may invent a plausible-looking number. `None` is an honest answer.

**Add descriptions** with `Field(description=...)` for anything ambiguous: units, formats, what to do in edge cases.

```python
from pydantic import BaseModel, Field

class Invoice(BaseModel):
    total: float = Field(description="Amount due including tax, as a plain number with no currency symbol")
    currency: str = Field(description="ISO 4217 code, e.g. NGN, USD, GBP")
    due_date: str | None = Field(description="YYYY-MM-DD. Null if the invoice does not state a due date")
```

**Choose types that match how you'll use the data.** Money as `float` is fine for extraction; convert to `Decimal` or integer kobo/cents before doing accounting. Dates as `"YYYY-MM-DD"` strings are easy for the model and easy to parse with `date.fromisoformat`.

**Keep it flat and focused.** A schema with 60 fields and five levels of nesting is harder for the model and for you. If a document has several distinct parts, consider several smaller extractions.

**Know what the API enforces.** The API guarantees structure (types, required keys, enums). Some JSON-schema constraints, such as numeric `minimum`/`maximum` or string lengths, aren't enforced during generation; the SDK moves them into the field's description as a hint, and Pydantic checks them when it validates. So keep `Field(ge=0)` and friends in your model: they're your safety net.

> **Try it:** Take the `Contact` model above, make `company` a required `str`, and run it on an email that doesn't mention a company. See what the model makes up. Then change it back to `str | None`.

## 6. Structured output and prompts work together

The schema says *what shape*; the prompt still says *what to do*. Keep instructions in the prompt:

- What the document is and where it came from.
- How to handle ambiguity ("if two totals appear, use the one labelled 'amount due'").
- Normalisation rules ("convert all amounts to numbers; drop thousands separators").

And keep wrapping the input in tags, exactly as in the prompting lesson. Structured output removes parsing problems, not thinking problems.

## Common mistakes

- **Parsing free text with regexes** when a schema would do.
- **Required fields for data that may be missing**, which invites the model to invent values.
- **Free-text fields for closed categories** instead of enums.
- **Too little `max_tokens`** for long lists, giving truncated output; check `stop_reason`.
- **Trusting valid JSON as correct data.** Add business-rule checks and spot-check real outputs.
- **Infinite retries.** Retry once or twice, then fail loudly.
- **Passing both `output_format` and `output_config["format"]`** on the same call.

## Recap

- Free text is unreliable for programs; structured output constrains replies to your JSON schema.
- `client.messages.parse(..., output_format=MyModel)` gives a validated object in `response.parsed_output`.
- The raw form is `output_config={"format": {"type": "json_schema", "schema": {...}}}` with `additionalProperties: false` and `required`.
- Handle `max_tokens`, refusals and `ValidationError`; retry a little, then fail clearly; add business-rule validation.
- Good schemas use enums with a catch-all, `X | None` for missing data, and descriptions for anything ambiguous.
