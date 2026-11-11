def build_summary_prompt(document: str, audience: str, max_words: int) -> str:
    """Document first (in <document> tags), then the instructions."""
    # TODO: validate document and max_words
    # TODO: return the prompt string (an f-string works well)
    raise NotImplementedError


def few_shot_examples(examples: list[tuple[str, str]]) -> str:
    """Format (input, output) pairs as an <examples> XML block."""
    # TODO: return "" for an empty list
    # TODO: build the lines and join them with "\n"
    raise NotImplementedError


if __name__ == "__main__":
    try:
        print(build_summary_prompt("Revenue rose 12% while costs fell.", "a busy CEO", 30))
        print()
        print(few_shot_examples([("I love it", "positive"), ("Broke in a day", "negative")]))
    except NotImplementedError:
        print("Fill in the TODOs, then Run again.")
