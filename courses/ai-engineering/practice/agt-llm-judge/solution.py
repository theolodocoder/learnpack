from typing import Literal

from pydantic import BaseModel, Field


class Verdict(BaseModel):
    reasoning: str
    score: int = Field(ge=1, le=5)
    passed: bool


class Preference(BaseModel):
    reasoning: str
    winner: Literal["first", "second", "tie"]


JUDGE_SYSTEM = (
    "You are a strict evaluator. Grade the answer ONLY against the rubric. "
    "First write your reasoning, then give a score from 1 (poor) to 5 (excellent) and whether it passes."
)
PAIR_SYSTEM = (
    "You compare two answers to the same question. Judge accuracy and helpfulness, not length or order. "
    "Reason first, then pick the better answer, or 'tie' if they are equally good."
)


def llm_judge(client, question: str, answer: str, rubric: str, model: str = "claude-opus-5-5") -> Verdict:
    """Grade one answer against a rubric. Returns a validated Verdict."""
    response = client.messages.parse(
        model=model,
        max_tokens=2000,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": (
            f"<question>\n{question}\n</question>\n<answer>\n{answer}\n</answer>\n<rubric>\n{rubric}\n</rubric>"
        )}],
        output_format=Verdict,
    )
    return response.parsed_output


def _prefer(client, question: str, first: str, second: str, model: str) -> str:
    response = client.messages.parse(
        model=model,
        max_tokens=2000,
        system=PAIR_SYSTEM,
        messages=[{"role": "user", "content": (
            f"<question>\n{question}\n</question>\n<first>\n{first}\n</first>\n<second>\n{second}\n</second>"
        )}],
        output_format=Preference,
    )
    return response.parsed_output.winner


def pairwise(client, question: str, answer_a: str, answer_b: str, model: str = "claude-opus-5-5") -> str:
    """Compare two answers twice, swapping their order. Returns "A", "B" or "tie"."""
    one = {"first": "A", "second": "B", "tie": "tie"}[_prefer(client, question, answer_a, answer_b, model)]
    two = {"first": "B", "second": "A", "tie": "tie"}[_prefer(client, question, answer_b, answer_a, model)]
    return one if one == two else "tie"
