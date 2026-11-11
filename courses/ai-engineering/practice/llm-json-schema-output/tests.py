import json

from fake_llm import FakeAnthropic, reply, text
from solution import TICKET_SCHEMA, Ticket, triage_ticket

GOOD = json.dumps({"category": "billing", "urgency": "high", "summary": "Charged twice"})


def test_schema_is_strict_and_complete():
    s = TICKET_SCHEMA
    assert s.get("type") == "object", "TICKET_SCHEMA needs \"type\": \"object\""
    assert s.get("additionalProperties") is False, "set \"additionalProperties\": False"
    assert set(s.get("required", [])) == {"category", "urgency", "summary"}, f"required should list all 3 fields, got {s.get('required')!r}"
    props = s.get("properties", {})
    assert set(props.get("category", {}).get("enum", [])) == {"billing", "bug", "feature", "other"}, "category needs an enum of the 4 categories"
    assert set(props.get("urgency", {}).get("enum", [])) == {"low", "medium", "high"}, "urgency needs an enum of low/medium/high"


def test_sends_output_config_with_schema():
    client = FakeAnthropic([reply(text(GOOD))])
    triage_ticket(client, "I was charged twice")
    oc = client.calls[0].get("output_config")
    want = {"format": {"type": "json_schema", "schema": TICKET_SCHEMA}}
    assert oc == want, f"expected output_config={want!r}, got {oc!r}"
    content = json.dumps(client.calls[0].get("messages"))
    assert "I was charged twice" in content, "the ticket text should be in your messages"


def test_returns_validated_ticket():
    client = FakeAnthropic([reply(text(GOOD))])
    got = triage_ticket(client, "I was charged twice")
    assert isinstance(got, Ticket), f"expected a Ticket, got {got!r}"
    assert (got.category, got.urgency) == ("billing", "high"), f"unexpected ticket: {got!r}"


def test_retries_once_after_invalid_output():
    bad = json.dumps({"category": "money", "urgency": "high", "summary": "x"})
    client = FakeAnthropic([reply(text(bad)), reply(text(GOOD))])
    got = triage_ticket(client, "I was charged twice")
    assert isinstance(got, Ticket), f"after one bad reply, the retry should succeed; got {got!r}"
    assert len(client.calls) == 2, f"expected 2 calls, got {len(client.calls)}"


def test_returns_none_after_two_failures():
    client = FakeAnthropic([reply(text("not json")), reply(text('{"category": "bug"}'))])
    got = triage_ticket(client, "help")
    assert got is None, f"two invalid replies should give None, got {got!r}"
    assert len(client.calls) == 2, f"stop after 2 attempts; made {len(client.calls)} calls"
