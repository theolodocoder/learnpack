from solution import (
    c_major_first_inversion,
    c_major_second_inversion,
    f_major_first_inversion,
    lowest_note_of_g_second_inversion,
)
from notes import same_note, same_notes


def test_c_major_first_inversion():
    assert same_notes(c_major_first_inversion, ["E", "G", "C"]), (
        "First inversion puts the third (E) on the bottom: E G C"
    )


def test_c_major_second_inversion():
    assert same_notes(c_major_second_inversion, ["G", "C", "E"]), (
        "Second inversion puts the fifth (G) on the bottom: G C E"
    )


def test_f_major_first_inversion():
    assert same_notes(f_major_first_inversion, ["A", "C", "F"]), (
        "F major is F A C; first inversion puts A on the bottom: A C F"
    )


def test_lowest_note_of_g_second_inversion():
    assert lowest_note_of_g_second_inversion and same_note(lowest_note_of_g_second_inversion, "D"), (
        "G major is G B D; second inversion puts the fifth (D) on the bottom"
    )
