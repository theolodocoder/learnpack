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


def test_half_step_up_from_e_is_f():
    assert note_is(half_step_up_from_e, "F"), (
        "There is no black key between E and F, so a half step up from E is F"
    )


def test_whole_step_up_from_e():
    assert note_is(whole_step_up_from_e, "F#"), (
        "A whole step is two half steps: E -> F -> F#. F# or Gb both count"
    )


def test_whole_step_down_from_c():
    assert note_is(whole_step_down_from_c, "Bb"), (
        "Going down two half steps: C -> B -> Bb. Bb or A# both count"
    )


def test_half_steps_from_c_to_g():
    assert half_steps_c_to_g == 7, (
        "Count the moves, not the keys: C#, D, D#, E, F, F#, G is 7 half steps"
    )
