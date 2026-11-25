from solution import groups, accents


def test_there_are_four_groups():
    assert len(groups) == 4, "12/8 is felt as four beats, so write four groups"


def test_each_group_has_three_pulses():
    assert len(groups) == 4 and all(len(g) == 3 for g in groups), \
        "Each felt beat in 12/8 is three eighth notes"


def test_pulses_run_from_one_to_twelve_in_order():
    flat = [p for g in groups for p in g]
    assert flat == list(range(1, 13)), "Count straight through: [1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]"


def test_accents_fall_on_the_first_of_each_group():
    assert list(accents) == [1, 4, 7, 10], "The strong pulses are 1, 4, 7 and 10: the start of each group"
