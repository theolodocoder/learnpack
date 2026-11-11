VAGUE_USERS = {"everyone", "anyone", "people", "users", "businesses", "all users"}


def check_spec(spec: dict) -> list[str]:
    """Return the problems with a one-page spec, in the order given in the task. [] means it passes."""
    problems: list[str] = []
    # TODO 1: "missing <key>" for user, job_to_be_done, success_metric (missing, not a str, or blank)
    # TODO 2: "user is too vague" if the user is in VAGUE_USERS
    # TODO 3: "success_metric has no number" if the metric has no digit
    # TODO 4: "need at least one non-goal"
    # TODO 5: "scope must be 1-3 weeks" (an int 1..3, and not a bool)
    return problems


if __name__ == "__main__":
    good = {
        "user": "Owners of small Lagos fashion shops who sell on WhatsApp",
        "job_to_be_done": "Answer repeat price and delivery questions without typing them out",
        "success_metric": "60% of customer questions answered without the owner in week 2",
        "non_goals": ["payments", "Instagram DMs"],
        "weeks": 3,
    }
    print(check_spec(good))
    print(check_spec({"user": "everyone", "success_metric": "users love it", "non_goals": [], "weeks": 6}))
