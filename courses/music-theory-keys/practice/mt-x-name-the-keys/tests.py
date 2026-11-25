from solution import *  # noqa
from notes import same_note, same_notes, gaps


def note_is(a, b):
    try:
        return same_note(a, b)
    except ValueError:
        return False


def notes_are(a, b):
    try:
        return same_notes(a, b)
    except ValueError:
        return False


def test_four_white_keys_and_five_black_keys():
    assert len(white_keys) == 4, "Give four white keys, for positions 2, 5, 9 and 11"
    assert len(black_keys) == 5, "Give five black keys, for positions 1, 3, 6, 8 and 10"


def test_white_keys_are_named_correctly():
    assert notes_are(white_keys, ["D", "F", "A", "B"]), (
        "Count up from C = 0: position 2 is D, 5 is F (E and F touch), 9 is A and 11 is B"
    )


def test_black_keys_are_named_correctly():
    assert notes_are(black_keys, ["C#", "D#", "F#", "G#", "A#"]), (
        "The black keys are C#/Db, D#/Eb, F#/Gb, G#/Ab and A#/Bb. Either spelling counts"
    )


def test_black_keys_use_a_sharp_or_a_flat():
    assert black_keys and all(len(str(n)) == 2 for n in black_keys), (
        "Every black key name has a letter plus # or b, like C# or Db"
    )
