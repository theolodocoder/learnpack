from typing import Literal

from pydantic import BaseModel, ValidationError


class Ticket(BaseModel):
    category: Literal["billing", "bug", "feature", "other"]
    urgency: Literal["low", "medium", "high"]
    summary: str


TICKET_SCHEMA: dict = {
    # TODO: "type", "properties" (with enums), "required", "additionalProperties"
}


def triage_ticket(client, text: str, model: str = "claude-opus-5-5") -> Ticket | None:
    """Classify a support ticket; retry once on invalid output, else return None."""
    # TODO: up to 2 attempts:
    #   call client.messages.create(..., output_config={"format": {"type": "json_schema", "schema": TICKET_SCHEMA}})
    #   join the text blocks; return Ticket.model_validate_json(raw)
    #   on ValidationError, try again
    # TODO: return None if both attempts failed
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    try:
        print(triage_ticket(anthropic.Anthropic(), "I was charged twice this month!!", model="claude-haiku-5-5"))
    except NotImplementedError:
        print("Write triage_ticket first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
