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


def test_d_major_has_two_sharps():
    assert sharps_in_d_major == 2, "D major has two sharps: F# and C#"


def test_b_flat_major_has_two_flats():
    assert flats_in_b_flat_major == 2, "Bb major has two flats: Bb and Eb"


def test_three_sharps_is_a_major():
    assert note_is(key_with_three_sharps, "A"), (
        "Three sharps are F#, C#, G#. The key is a half step above the last sharp: A"
    )


def test_next_key_clockwise_after_g_is_d():
    assert note_is(next_key_clockwise_after_g, "D"), (
        "Clockwise means up a fifth (7 half steps): G -> D, which adds one sharp"
    )
