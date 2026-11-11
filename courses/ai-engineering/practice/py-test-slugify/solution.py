import re


def slugify(text: str) -> str:
    """'Hello, World!' -> 'hello-world'."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def test_simple_title():
    assert slugify("Hello World") == "hello-world"


def test_lowercases_everything():
    assert slugify("RAG") == "rag"


def test_collapses_runs_of_separators():
    assert slugify("a  --  b") == "a-b"


def test_strips_dashes_from_both_ends():
    assert slugify("  -hello-  ") == "hello"


def test_removes_punctuation():
    assert slugify("Hi, there!") == "hi-there"


def test_empty_string_stays_empty():
    assert slugify("") == ""


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except AssertionError as e:
            print("FAIL", t.__name__, e)
