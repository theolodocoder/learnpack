def merge_slots(slots: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Merge overlapping or touching ("HH:MM", "HH:MM") slots into sorted, non-overlapping blocks."""
    for start, end in slots:
        if start >= end:
            raise ValueError(f"slot starts at or after it ends: {(start, end)}")
    merged: list[tuple[str, str]] = []
    for start, end in sorted(slots):  # zero-padded "HH:MM" sorts in time order
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


if __name__ == "__main__":
    busy = [("13:00", "14:00"), ("09:00", "10:30"), ("10:00", "11:00"), ("13:30", "13:45")]
    print(merge_slots(busy))  # [('09:00', '11:00'), ('13:00', '14:00')]
