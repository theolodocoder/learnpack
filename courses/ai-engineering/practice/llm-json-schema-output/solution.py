from typing import Literal

from pydantic import BaseModel, ValidationError


class Ticket(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
    urgency: Literal["low", "medium", "high"]
    summary: str


TICKET_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["billing", "bug", "feature", "other"]},
        "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
        "summary": {"type": "string", "description": "One sentence describing the problem"},
    },
    "required": ["category", "urgency", "summary"],
    "additionalProperties": False,
}


def triage_ticket(client, text: str, model: str = "claude-opus-5-5") -> Ticket | None:
    """Classify a support ticket; retry once on invalid output, else return None."""
    for _ in range(2):
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": f"Triage this support ticket.\n\n<ticket>\n{text}\n</ticket>"}],
            output_config={"format": {"type": "json_schema", "schema": TICKET_SCHEMA}},
        )
        raw = "".join(b.text for b in response.content if b.type == "text")
        try:
            return Ticket.model_validate_json(raw)
        except ValidationError:
            continue
    return None
