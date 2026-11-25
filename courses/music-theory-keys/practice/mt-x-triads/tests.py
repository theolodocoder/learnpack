from solution import c_major, a_minor, d_major, b_diminished, quality_of_e_g_b
from notes import gaps, same_notes


def check(chord, expected, shape, label):
    assert len(chord) == 3, f"{label} has three notes: root, third, fifth"
    assert gaps(chord) == shape, f"{label} should be {shape[0]} then {shape[1]} half steps; yours is {gaps(chord)}"
    assert same_notes(chord, expected), f"{label} is {' '.join(expected)}, starting on the root"


def test_c_major():
    check(c_major, ["C", "E", "G"], [4, 3], "C major")


def test_a_minor():
    check(a_minor, ["A", "C", "E"], [3, 4], "A minor")


def test_d_major_has_f_sharp():
    check(d_major, ["D", "F#", "A"], [4, 3], "D major (F# is the third, not F)")


def test_b_diminished():
    check(b_diminished, ["B", "D", "F"], [3, 3], "B diminished")


def test_e_g_b_is_minor():
    assert " ".join(str(quality_of_e_g_b).lower().split()) == "minor", (
        "E to G is 3 half steps and G to B is 4: that's minor"
    )
