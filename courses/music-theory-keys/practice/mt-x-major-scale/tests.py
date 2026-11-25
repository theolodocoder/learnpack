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

MAJOR = [2, 2, 1, 2, 2, 2, 1]


def check(scale, root, hint):
    assert len(scale) == 7, f"Write 7 notes for {root} major, from {root} up to the 7th"
    assert note_is(scale[0], root), f"{root} major starts on {root}"
    try:
        steps = gaps(list(scale) + [scale[0]])
    except ValueError:
        steps = None
    assert steps == MAJOR, f"Follow W W H W W W H. {hint}"


def test_g_major_follows_the_formula():
    check(g_major, "G", "G major has one sharp: F#")


def test_f_major_follows_the_formula():
    check(f_major, "F", "F major has one flat: Bb")


def test_d_major_follows_the_formula():
    check(d_major, "D", "D major has two sharps: F# and C#")


def test_each_scale_uses_every_letter_once():
    for name, scale in [("G major", g_major), ("F major", f_major), ("D major", d_major)]:
        letters = sorted(str(n).strip()[:1].upper() for n in scale)
        assert letters == list("ABCDEFG"), (
            f"{name} must use each letter A to G exactly once. "
            "For example, F major has Bb, not A#"
        )
