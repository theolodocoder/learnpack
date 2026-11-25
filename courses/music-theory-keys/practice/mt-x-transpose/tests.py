from solution import up_whole_step, in_b_flat, half_steps_from_g_to_bb
from notes import same_chord


def _match(given, expected):
    return len(given) == len(expected) and all(same_chord(g, e) for g, e in zip(given, expected))


def test_up_a_whole_step():
    assert _match(up_whole_step, ["D", "Bm", "G", "A"]), \
        "Move every root up two half steps: C->D, A->B, F->G, G->A. Am stays minor, so it becomes Bm"


def test_in_b_flat():
    assert _match(in_b_flat, ["Bb", "Gm", "Eb", "F"]), \
        "C Am F G is 1-6-4-5. In Bb (Bb C D Eb F G A): 1 = Bb, 6 = Gm, 4 = Eb, 5 = F"


def test_qualities_are_kept():
    assert len(up_whole_step) == 4 and str(up_whole_step[1]).strip().endswith("m"), \
        "Transposing moves the roots only: the second chord is still minor"


def test_half_steps_g_to_b_flat():
    assert half_steps_from_g_to_bb == 3, "Count the keys: G -> G# -> A -> Bb is 3 half steps"
