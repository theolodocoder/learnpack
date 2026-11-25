from solution import beats, eighth_notes_in_bar_of_6_8, beat_groups_in_12_8

ALLOWED = {2, 1, 0.5, 0.25}


def test_bar_adds_up_to_four_beats():
    assert len(beats) > 0 and sum(beats) == 4, \
        f"A bar of 4/4 holds 4 quarter-note beats; your values add up to {sum(beats)}"


def test_only_uses_known_note_values():
    assert len(beats) > 0 and all(b in ALLOWED for b in beats), \
        "Use only 2 (half), 1 (quarter), 0.5 (eighth) and 0.25 (sixteenth)"


def test_uses_at_least_three_different_values():
    assert len(set(beats)) >= 3, "Mix it up: use at least three different note values"


def test_eighths_in_six_eight():
    assert eighth_notes_in_bar_of_6_8 == 6, "6/8 means six eighth notes in every bar"


def test_beat_groups_in_twelve_eight():
    assert beat_groups_in_12_8 == 4, "12 eighth notes in groups of three: 12 / 3 = 4 felt beats"
