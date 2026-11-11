def merge_slots(slots: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Merge overlapping or touching ("HH:MM", "HH:MM") slots into sorted, non-overlapping blocks."""
    # TODO: raise ValueError for any slot whose start is not before its end
    # TODO: sort a copy of the slots by start time
    # TODO: walk through them, extending the last merged block or starting a new one
    return []


if __name__ == "__main__":
    busy = [("13:00", "14:00"), ("09:00", "10:30"), ("10:00", "11:00"), ("13:30", "13:45")]
    print(merge_slots(busy))  # [('09:00', '11:00'), ('13:00', '14:00')]
