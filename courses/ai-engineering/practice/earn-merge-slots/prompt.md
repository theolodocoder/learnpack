# Merge overlapping time slots

A practical interval problem you might get in a live-coding round: a scheduling assistant collects busy times from several calendars and needs one clean list of busy blocks.

Times are `"HH:MM"` strings in 24-hour format, always zero-padded (`"09:05"`, not `"9:05"`). Each slot is a `(start, end)` tuple.

Write:

```python
def merge_slots(slots: list[tuple[str, str]]) -> list[tuple[str, str]]: ...
```

1. Return the slots merged into the fewest non-overlapping blocks, sorted by start time.
2. Slots that **overlap** merge, and so do slots that **touch** (`("09:00", "10:00")` and `("10:00", "11:00")` become `("09:00", "11:00")`).
3. A slot inside another disappears into it.
4. The input may be in any order. An empty list returns an empty list.
5. If any slot has `start >= end`, raise `ValueError`.
6. Don't modify the input list.

Hint: zero-padded `"HH:MM"` strings sort in time order as plain strings, so you can compare them directly. Sort by start, then walk through once, extending the last block or starting a new one. That's O(n log n) for the sort and O(n) for the walk.

## Example

```python
merge_slots([("13:00", "14:00"), ("09:00", "10:30"), ("10:00", "11:00"), ("13:30", "13:45")])
# [("09:00", "11:00"), ("13:00", "14:00")]
```
