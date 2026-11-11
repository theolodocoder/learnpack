def build_messages(history: list[tuple[str, str]], new_message: str) -> list[dict]:
    """Turn (user, assistant) pairs plus a new user message into the API's messages list."""
    # TODO: raise ValueError if new_message is blank
    # TODO: add a user dict and an assistant dict for each pair
    # TODO: finish with the new user message
    raise NotImplementedError


if __name__ == "__main__":
    try:
        print(build_messages([("Hi", "Hello! How can I help?")], "What's 2 + 2?"))
    except NotImplementedError:
        print("Fill in the TODOs, then Run again.")
