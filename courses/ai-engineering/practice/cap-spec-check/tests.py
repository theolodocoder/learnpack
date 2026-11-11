from solution import check_spec

GOOD = {
    "user": "Owners of small Lagos fashion shops who sell on WhatsApp",
    "job_to_be_done": "Answer repeat price and delivery questions without typing them out",
    "success_metric": "60% of customer questions answered without the owner in week 2",
    "non_goals": ["payments", "Instagram DMs"],
    "weeks": 3,
}


def test_a_good_spec_has_no_problems():
    got = check_spec(dict(GOOD))
    assert got == [], f"expected [], got {got!r}"


def test_reports_missing_and_blank_fields():
    spec = dict(GOOD, job_to_be_done="   ")
    del spec["user"]
    got = check_spec(spec)
    want = ["missing user", "missing job_to_be_done"]
    assert got == want, f"expected {want!r}, got {got!r}"
    got = check_spec(dict(GOOD, success_metric=42))
    assert got == ["missing success_metric"], f"a non-string metric counts as missing, got {got!r}"


def test_flags_vague_user_and_metric_without_a_number():
    got = check_spec(dict(GOOD, user="  Everyone "))
    assert got == ["user is too vague"], f"expected ['user is too vague'], got {got!r}"
    got = check_spec(dict(GOOD, success_metric="users are happy"))
    assert got == ["success_metric has no number"], f"expected ['success_metric has no number'], got {got!r}"


def test_non_goals_must_have_a_real_entry():
    for bad in ([], ["  "], "payments", None):
        got = check_spec(dict(GOOD, non_goals=bad))
        assert got == ["need at least one non-goal"], f"non_goals={bad!r}: expected the non-goal problem, got {got!r}"


def test_weeks_must_be_an_int_from_1_to_3():
    for bad in (0, 4, 2.5, "3", True, None):
        got = check_spec(dict(GOOD, weeks=bad))
        assert got == ["scope must be 1-3 weeks"], f"weeks={bad!r}: expected the scope problem, got {got!r}"
    spec = dict(GOOD)
    del spec["weeks"]
    assert check_spec(spec) == ["scope must be 1-3 weeks"], "a missing weeks value should be a problem"


def test_reports_every_problem_in_order():
    got = check_spec({"user": "everyone", "success_metric": "users love it", "non_goals": [], "weeks": 6})
    want = ["missing job_to_be_done", "user is too vague", "success_metric has no number",
            "need at least one non-goal", "scope must be 1-3 weeks"]
    assert got == want, f"expected {want!r}, got {got!r}"
