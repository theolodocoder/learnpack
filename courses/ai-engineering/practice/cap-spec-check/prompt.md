# Check a one-page product spec

Before you build, your spec should name a real user, the job they need done, a success metric you can measure, at least one non-goal, and a scope that fits the capstone's three weeks. Write a checker that catches the usual gaps.

Write:

```python
def check_spec(spec: dict) -> list[str]:
```

It returns a list of problems, in this order (an empty list means the spec passes):

1. For each of `"user"`, `"job_to_be_done"` and `"success_metric"`: if the key is missing, isn't a string, or is blank after `.strip()`, add `"missing <key>"` (for example `"missing user"`).
2. If `user` is present but, lowercased and stripped, is one of `VAGUE_USERS` (given in the starter: `"everyone"`, `"anyone"`, `"people"`, `"users"`, `"businesses"`, `"all users"`), add `"user is too vague"`.
3. If `success_metric` is present but contains no digit, add `"success_metric has no number"`. A metric you can't count isn't a metric.
4. If `non_goals` isn't a list containing at least one non-blank string, add `"need at least one non-goal"`.
5. If `weeks` isn't an `int` from 1 to 3 (inclusive), add `"scope must be 1-3 weeks"`. A missing `weeks` counts too. `True` is not a number of weeks: reject `bool`.

## Example

```python
spec = {
    "user": "Owners of small Lagos fashion shops who sell on WhatsApp",
    "job_to_be_done": "Answer repeat price and delivery questions without typing them out",
    "success_metric": "60% of customer questions answered without the owner in week 2",
    "non_goals": ["payments", "Instagram DMs"],
    "weeks": 3,
}
check_spec(spec)   # []

check_spec({"user": "everyone", "success_metric": "users love it", "non_goals": [], "weeks": 6})
# ['missing job_to_be_done', 'user is too vague', 'success_metric has no number',
#  'need at least one non-goal', 'scope must be 1-3 weeks']
```
