from solution import build_summary_prompt, few_shot_examples

DOC = "Q3 revenue rose 12% to 4.1M naira. Logistics costs fell 3%."


def test_document_is_wrapped_in_tags():
    p = build_summary_prompt(DOC, "the finance team", 50)
    want = f"<document>\n{DOC}\n</document>"
    assert want in p, f"expected the document wrapped as {want!r} in:\n{p}"


def test_instructions_mention_audience_and_limit_after_document():
    p = build_summary_prompt(DOC, "the finance team", 50)
    assert "the finance team" in p, "the prompt should mention the audience"
    assert "50" in p, "the prompt should include the word limit"
    assert p.index("</document>") < p.index("the finance team"), "put the instructions after the document"


def test_document_appears_once():
    p = build_summary_prompt(DOC, "a CEO", 20)
    assert p.count(DOC) == 1, f"the document text should appear exactly once, found {p.count(DOC)} times"


def test_rejects_bad_input():
    for args in [("   ", "a CEO", 20), (DOC, "a CEO", 0)]:
        try:
            build_summary_prompt(*args)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for build_summary_prompt{args!r}")


def test_few_shot_format_is_exact():
    got = few_shot_examples([("I love it", "positive"), ("Broke in a day", "negative")])
    want = (
        "<examples>\n<example>\n<input>I love it</input>\n<output>positive</output>\n</example>\n"
        "<example>\n<input>Broke in a day</input>\n<output>negative</output>\n</example>\n</examples>"
    )
    assert got == want, f"expected:\n{want}\n\ngot:\n{got}"


def test_few_shot_empty_list_is_empty_string():
    got = few_shot_examples([])
    assert got == "", f"expected '', got {got!r}"
