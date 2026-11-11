from pydantic import BaseModel


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


def extract_invoice(client, text: str, model: str = "claude-opus-5-5") -> Invoice:
    """Extract a validated Invoice from raw invoice text."""
    # TODO: call client.messages.parse(..., output_format=Invoice)
    #       with one user message containing an instruction and <invoice>\n{text}\n</invoice>
    # TODO: return response.parsed_output
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    sample = """ACME Ltd                     Invoice INV-0042
2 x Widget @ 1,500 NGN
1 x Delivery @ 500 NGN
Total: NGN 3,500
Payment due 1 Dec 2026"""
    try:
        print(extract_invoice(anthropic.Anthropic(), sample, model="claude-haiku-5-5").model_dump_json(indent=2))
    except NotImplementedError:
        print("Write extract_invoice first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
