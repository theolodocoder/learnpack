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


def test_relative_minor_of_c_is_a():
    assert note_is(relative_minor_of_c, "A"), (
        "The 6th note of C major is A, three half steps below C"
    )


def test_relative_minor_of_g_is_e():
    assert note_is(relative_minor_of_g, "E"), (
        "G major is G A B C D E F#. The 6th note is E (G down 3 half steps: F#, F, E)"
    )


def test_relative_major_of_d_minor_is_f():
    assert note_is(relative_major_of_d_minor, "F"), (
        "Go three half steps up from D: Eb, E, F"
    )


def test_a_natural_minor_scale():
    assert notes_are(a_natural_minor, ["A", "B", "C", "D", "E", "F", "G"]), (
        "A natural minor uses only white keys: A B C D E F G, the same notes as C major"
    )
