from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float


class Invoice(BaseModel):
    vendor: str = Field(description="Company that issued the invoice")
    invoice_number: str
    currency: str = Field(description="ISO 4217 code, e.g. NGN or USD")
    total: float = Field(description="Amount due, as a plain number")
    due_date: str | None = Field(description="YYYY-MM-DD, or null if not stated")
    line_items: list[LineItem]


def extract_invoice(client, text: str, model: str = "claude-opus-5-5") -> Invoice:
    """Extract a validated Invoice from raw invoice text."""
    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": f"Extract the invoice details from the text below.\n\n<invoice>\n{text}\n</invoice>",
        }],
        output_format=Invoice,
    )
    return response.parsed_output
