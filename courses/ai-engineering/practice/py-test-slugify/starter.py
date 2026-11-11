import re


def slugify(text: str) -> str:
    """'Hello, World!' -> 'hello-world'."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# Write your tests below. Each one: arrange an input, act (call slugify), assert the result.

def test_simple_title():
    assert slugify("Hello World") == "hello-world"


# TODO: add tests for lowercase, collapsing runs, no leading/trailing dashes, punctuation


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError as e:
            print("FAIL", t.__name__, e)
