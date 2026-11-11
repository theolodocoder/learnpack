import json

from fake_llm import FakeAnthropic, reply, text
from solution import Invoice, extract_invoice

DATA = {
    "vendor": "ACME Ltd", "invoice_number": "INV-0042", "currency": "NGN", "total": 3500,
    "due_date": "2026-12-01",
    "line_items": [
        {"description": "Widget", "quantity": 2, "unit_price": 1500},
        {"description": "Delivery", "quantity": 1, "unit_price": 500},
    ],
}
RAW = "ACME Ltd  INV-0042\n2 x Widget @ 1,500\n1 x Delivery @ 500\nTotal NGN 3,500"


def run(data=DATA, raw=RAW):
    client = FakeAnthropic([reply(text(json.dumps(data)))])
    return client, extract_invoice(client, raw)


def test_returns_an_invoice():
    _, inv = run()
    assert isinstance(inv, Invoice), f"expected an Invoice instance, got {type(inv).__name__}"
    assert inv.vendor == "ACME Ltd" and inv.total == 3500, f"unexpected fields: {inv!r}"


def test_line_items_are_parsed():
    _, inv = run()
    assert len(inv.line_items) == 2, f"expected 2 line items, got {len(inv.line_items)}"
    first = inv.line_items[0]
    assert (first.description, first.quantity, first.unit_price) == ("Widget", 2, 1500.0), f"unexpected first item: {first!r}"


def test_uses_parse_with_invoice_as_output_format():
    client, _ = run()
    sent = client.calls[0]
    assert sent.get("output_format") is Invoice, f"pass output_format=Invoice, got {sent.get('output_format')!r}"
    assert sent.get("model"), "send a model"
    assert isinstance(sent.get("max_tokens"), int) and sent["max_tokens"] > 0, "send a positive max_tokens"


def test_invoice_text_is_wrapped_in_tags():
    client, _ = run()
    msgs = client.calls[0].get("messages") or []
    assert len(msgs) == 1 and msgs[0].get("role") == "user", f"send exactly one user message, got {msgs!r}"
    assert f"<invoice>\n{RAW}\n</invoice>" in msgs[0]["content"], "wrap the text as <invoice>\\n...\\n</invoice>"


def test_missing_due_date_is_none():
    _, inv = run({**DATA, "due_date": None})
    assert inv.due_date is None, f"expected due_date None, got {inv.due_date!r}"
