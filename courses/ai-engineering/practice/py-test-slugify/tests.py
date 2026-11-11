import re

import solution

CORRECT = solution.slugify


def no_lowercase(text):
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-")


def no_collapse(text):
    return re.sub(r"[^a-z0-9]", "-", text.lower()).strip("-")


def no_strip(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower())


def keeps_punctuation(text):
    return re.sub(r"\s+", "-", text.lower()).strip("-")


def _learner_tests():
    return [f for name, f in vars(solution).items() if name.startswith("test_") and callable(f)]


def _failures_with(impl):
    """Run the learner's tests with solution.slugify swapped for `impl`; return names that failed."""
    solution.slugify = impl
    failed = []
    try:
        for t in _learner_tests():
            try:
                t()
            except Exception:
                failed.append(t.__name__)
    finally:
        solution.slugify = CORRECT
    return failed


def test_you_wrote_at_least_three_tests():
    n = len(_learner_tests())
    assert n >= 3, f"write at least 3 functions named test_..., found {n}"


def test_your_tests_pass_on_the_correct_slugify():
    failed = _failures_with(CORRECT)
    assert not failed, f"these tests fail on the correct slugify, so they expect the wrong thing: {failed}"


def test_your_tests_catch_missing_lowercase():
    assert _failures_with(no_lowercase), "none of your tests failed when slugify stopped lowercasing"


def test_your_tests_catch_uncollapsed_separators():
    assert _failures_with(no_collapse), "none of your tests failed when 'a  b' became 'a--b'"


def test_your_tests_catch_leftover_edge_dashes():
    assert _failures_with(no_strip), "none of your tests failed when slugify left '-' at the start or end"


def test_your_tests_catch_kept_punctuation():
    assert _failures_with(keeps_punctuation), "none of your tests failed when slugify kept punctuation like '!'"
