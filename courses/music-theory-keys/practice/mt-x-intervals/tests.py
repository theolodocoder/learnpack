from solution import c_to_e_half_steps, c_to_e_name, a_to_c_name, c_to_g_name, perfect_fourth_above_d
from notes import same_note


def norm(name):
    return " ".join(str(name).lower().split())


def test_c_to_e_is_four_half_steps():
    assert c_to_e_half_steps == 4, "Count from C without counting C itself: C#, D, D#, E is 4 half steps"


def test_c_to_e_is_a_major_third():
    assert norm(c_to_e_name) == "major third", "4 half steps is a major third"


def test_a_to_c_is_a_minor_third():
    assert norm(a_to_c_name) == "minor third", "A, A#, B, C is 3 half steps: a minor third"


def test_c_to_g_is_a_perfect_fifth():
    assert norm(c_to_g_name) == "perfect fifth", "C up to G is 7 half steps: a perfect fifth"


def test_perfect_fourth_above_d_is_g():
    assert perfect_fourth_above_d and same_note(perfect_fourth_above_d, "G"), (
        "A perfect fourth is 5 half steps: D#, E, F, F#, G"
    )
