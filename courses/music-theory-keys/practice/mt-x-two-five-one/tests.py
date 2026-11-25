from solution import f_251, bb_251
from notes import chord_root, same_note

SUFFIXES = ["m7", "7", "maj7"]


def _roots_ok(chords, roots):
    return len(chords) == len(roots) and all(same_note(chord_root(c), r) for c, r in zip(chords, roots))


def _suffixes(chords):
    return [str(c).strip()[len(chord_root(c)):] for c in chords]


def test_roots_in_f():
    assert _roots_ok(f_251, ["G", "C", "F"]), "F major is F G A Bb C D E, so 2 = G, 5 = C, 1 = F"


def test_suffixes_in_f():
    assert len(f_251) == 3 and _suffixes(f_251) == SUFFIXES, "2-5-1 is m7, 7, maj7: Gm7 C7 Fmaj7"


def test_roots_in_b_flat():
    assert _roots_ok(bb_251, ["C", "F", "Bb"]), "Bb major is Bb C D Eb F G A, so 2 = C, 5 = F, 1 = Bb"


def test_suffixes_in_b_flat():
    assert len(bb_251) == 3 and _suffixes(bb_251) == SUFFIXES, "2-5-1 is m7, 7, maj7: Cm7 F7 Bbmaj7"
