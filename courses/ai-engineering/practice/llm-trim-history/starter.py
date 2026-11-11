import math


def estimate_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 4 characters, rounded up."""
    # TODO: return ceil(len(text) / 4)
    raise NotImplementedError


def trim_history(messages: list[dict], budget: int) -> list[dict]:
    """Keep the newest messages that fit in `budget` tokens; result must start with a user message."""
    # TODO: walk the messages from newest to oldest, adding each one while the total fits
    # TODO: put the kept messages back in their original order
    # TODO: drop assistant messages at the front
    raise NotImplementedError


if __name__ == "__main__":
    msgs = [
        {"role": "user", "content": "a" * 40},
        {"role": "assistant", "content": "b" * 40},
        {"role": "user", "content": "c" * 20},
    ]
    try:
        print(estimate_tokens("hello world"))  # 3
        print(trim_history(msgs, 15))
    except NotImplementedError:
        print("Fill in the TODOs, then Run again.")
