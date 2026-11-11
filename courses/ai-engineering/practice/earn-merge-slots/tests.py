from solution import merge_slots


def test_example_from_the_prompt():
    got = merge_slots([("13:00", "14:00"), ("09:00", "10:30"), ("10:00", "11:00"), ("13:30", "13:45")])
    want = [("09:00", "11:00"), ("13:00", "14:00")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_separate_slots_stay_separate_and_sorted():
    got = merge_slots([("15:00", "16:00"), ("08:00", "09:00")])
    want = [("08:00", "09:00"), ("15:00", "16:00")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_touching_slots_merge():
    got = merge_slots([("09:00", "10:00"), ("10:00", "11:00")])
    want = [("09:00", "11:00")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_slot_inside_another_is_absorbed():
    got = merge_slots([("09:00", "17:00"), ("12:00", "13:00"), ("16:30", "17:00")])
    want = [("09:00", "17:00")]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_empty_list_and_input_not_modified():
    assert merge_slots([]) == [], f"expected [], got {merge_slots([])!r}"
    slots = [("11:00", "12:00"), ("09:00", "11:30")]
    copy = list(slots)
    merge_slots(slots)
    assert slots == copy, f"the input list was modified: {slots!r}"


def test_rejects_slot_that_ends_before_it_starts():
    for bad in [("10:00", "09:00"), ("10:00", "10:00")]:
        try:
            merge_slots([("08:00", "09:00"), bad])
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for slot {bad!r}")
