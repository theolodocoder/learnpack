VAGUE_USERS = {"everyone", "anyone", "people", "users", "businesses", "all users"}


def _filled(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def check_spec(spec: dict) -> list[str]:
    """Return the problems with a one-page spec, in the order given in the task. [] means it passes."""
    problems = [f"missing {key}" for key in ("user", "job_to_be_done", "success_metric")
                if not _filled(spec.get(key))]

    user = spec.get("user")
    if _filled(user) and user.strip().lower() in VAGUE_USERS:
        problems.append("user is too vague")

    metric = spec.get("success_metric")
    if _filled(metric) and not any(ch.isdigit() for ch in metric):
        problems.append("success_metric has no number")

    non_goals = spec.get("non_goals")
    if not (isinstance(non_goals, list) and any(_filled(g) for g in non_goals)):
        problems.append("need at least one non-goal")

    weeks = spec.get("weeks")
    if not (isinstance(weeks, int) and not isinstance(weeks, bool) and 1 <= weeks <= 3):
        problems.append("scope must be 1-3 weeks")

    return problems


if __name__ == "__main__":
    print(check_spec({"user": "everyone", "success_metric": "users love it", "non_goals": [], "weeks": 6}))
