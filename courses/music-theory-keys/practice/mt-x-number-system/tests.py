from solution import g_1564, d_145, c_251, diatonic_triads_in_c
from notes import same_chord, chord_root, same_note


def _match(given, expected):
    if len(given) != len(expected):
        return False
    for g, e in zip(given, expected):
        g = str(g).strip().replace("°", "dim")
        if g.lower().endswith("o") and not g.lower().endswith("dim"):
            g = g[:-1] + "dim"
        if not same_chord(g, e):
            return False
    return True


def test_one_five_six_four_in_g():
    assert _match(g_1564, ["G", "D", "Em", "C"]), \
        "G major is G A B C D E F#. 1 = G, 5 = D, 6 = E (a minor chord: Em), 4 = C"


def test_one_four_five_in_d():
    assert _match(d_145, ["D", "G", "A"]), \
        "D major is D E F# G A B C#. 1 = D, 4 = G, 5 = A, and all three are major"


def test_two_five_one_in_c():
    assert _match(c_251, ["Dm", "G", "C"]), \
        "In C, 2 = D (minor, so Dm), 5 = G, 1 = C"


def test_all_seven_chords_in_c():
    assert len(diatonic_triads_in_c) == 7, "There are seven chords: one on each note of C major"
    assert _match(diatonic_triads_in_c, ["C", "Dm", "Em", "F", "G", "Am", "Bdim"]), \
        "Pattern: 1 major, 2 minor, 3 minor, 4 major, 5 major, 6 minor, 7 diminished -> C Dm Em F G Am Bdim"
