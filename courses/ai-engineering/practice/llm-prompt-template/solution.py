def build_summary_prompt(document: str, audience: str, max_words: int) -> str:
    """Document first (in <document> tags), then the instructions."""
    if not document.strip():
        raise ValueError("document must not be empty")
    if max_words < 1:
        raise ValueError("max_words must be at least 1")
    return (
        f"<document>\n{document}\n</document>\n\n"
        f"Summarise the document above for {audience}. "
        f"Use at most {max_words} words. Keep only the points this reader needs to act on."
    )


def few_shot_examples(examples: list[tuple[str, str]]) -> str:
    """Format (input, output) pairs as an <examples> XML block."""
    if not examples:
        return ""
    lines = ["<examples>"]
    for inp, out in examples:
        lines += ["<example>", f"<input>{inp}</input>", f"<output>{out}</output>", "</example>"]
    lines.append("</examples>")
    return "\n".join(lines)
