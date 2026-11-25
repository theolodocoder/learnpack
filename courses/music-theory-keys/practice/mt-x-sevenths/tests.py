from solution import cmaj7, dm7, g7, asus4, chord_with_gaps_4_3_3
from notes import gaps, same_notes


def check(chord, expected, shape, label):
    assert len(chord) == len(expected), f"{label} has {len(expected)} notes"
    assert gaps(chord) == shape, f"{label} should have gaps {shape}; yours has {gaps(chord)}"
    assert same_notes(chord, expected), f"{label} is {' '.join(expected)}, starting on the root"


def test_c_major_7():
    check(cmaj7, ["C", "E", "G", "B"], [4, 3, 4], "Cmaj7 (major 7th B, not Bb)")


def test_d_minor_7():
    check(dm7, ["D", "F", "A", "C"], [3, 4, 3], "Dm7")


def test_g_dominant_7():
    check(g7, ["G", "B", "D", "F"], [4, 3, 3], "G7 (minor 7th F, not F#)")


def test_a_sus4():
    check(asus4, ["A", "D", "E"], [5, 2], "Asus4 (the 4th D replaces the third)")


def test_4_3_3_is_dominant_7():
    name = " ".join(str(chord_with_gaps_4_3_3).lower().split()).replace("seventh", "7")
    assert name == "dominant 7", "4 3 3 is a major triad with a minor 7th on top: dominant 7"
