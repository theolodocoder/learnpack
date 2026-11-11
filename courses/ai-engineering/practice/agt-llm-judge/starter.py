from typing import Literal

from pydantic import BaseModel, Field


class Verdict(BaseModel):
    reasoning: str
    score: int  # TODO: constrain to 1..5 with Field(ge=1, le=5)
    passed: bool


class Preference(BaseModel):
    reasoning: str
    winner: Literal["first", "second", "tie"]


def llm_judge(client, question: str, answer: str, rubric: str, model: str = "claude-opus-5-5") -> Verdict:
    """Grade one answer against a rubric. Returns a validated Verdict."""
    # TODO: one client.messages.parse(..., output_format=Verdict) call
    #       with <question>, <answer> and <rubric> tags in the user message
    raise NotImplementedError


def pairwise(client, question: str, answer_a: str, answer_b: str, model: str = "claude-opus-5-5") -> str:
    """Compare two answers twice, swapping their order. Returns "A", "B" or "tie"."""
    # TODO: call 1 with A in <first>, B in <second>; call 2 swapped
    # TODO: map "first"/"second" back to "A"/"B"; agree -> that result, disagree -> "tie"
    raise NotImplementedError


if __name__ == "__main__":
    import anthropic

    client = anthropic.Anthropic()
    try:
        v = llm_judge(client, "How do I reset my password?",
                      "Click 'Forgot password' on the login page and follow the email link.",
                      "Pass if the answer gives concrete steps and is polite. Score 1-5 for helpfulness.",
                      model="claude-haiku-5-5")
        print(v)
    except NotImplementedError:
        print("Write llm_judge first, then Run again.")
    except anthropic.AnthropicError as e:
        print("API call failed (is ANTHROPIC_API_KEY set?):", e)
