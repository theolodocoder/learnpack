from solution import with_sevenths, in_g_with_sevenths
from notes import chord_root, same_note

SUFFIXES = ["maj7", "m7", "m7", "7"]


def _roots_ok(chords, roots):
    return len(chords) == len(roots) and all(same_note(chord_root(c), r) for c, r in zip(chords, roots))


def _suffixes(chords):
    return [str(c).strip()[len(chord_root(c)):] for c in chords]


def test_roots_in_c_are_one_six_two_five():
    assert _roots_ok(with_sevenths, ["C", "A", "D", "G"]), "1-6-2-5 in C has the roots C, A, D, G"


def test_sevenths_in_c_use_the_right_suffixes():
    assert len(with_sevenths) == 4 and _suffixes(with_sevenths) == SUFFIXES, \
        "1 gets maj7, 6 and 2 get m7, 5 gets a plain 7: Cmaj7 Am7 Dm7 G7"


def test_roots_in_g_are_one_six_two_five():
    assert _roots_ok(in_g_with_sevenths, ["G", "E", "A", "D"]), \
        "G major is G A B C D E F#, so 1 = G, 6 = E, 2 = A, 5 = D"


def test_sevenths_in_g_use_the_right_suffixes():
    assert len(in_g_with_sevenths) == 4 and _suffixes(in_g_with_sevenths) == SUFFIXES, \
        "Same pattern in every key: Gmaj7 Em7 Am7 D7"
