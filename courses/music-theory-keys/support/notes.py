"""Note helpers shared by the hidden tests. Learners never need to import this."""

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def pitch_class(note):
    """'C#' -> 1, 'db' -> 1, 'B#' -> 0, 'Cb' -> 11. Accepts ♯/♭ and any case."""
    s = str(note).strip().replace("♯", "#").replace("♭", "b")
    if not s or s[0].upper() not in _PC:
        raise ValueError(f"not a note name: {note!r}")
    n = _PC[s[0].upper()]
    for ch in s[1:]:
        if ch == "#":
            n += 1
        elif ch == "b":
            n -= 1
        else:
            raise ValueError(f"not a note name: {note!r}")
    return n % 12


def same_note(a, b):
    """True when two spellings sound the same (C# and Db)."""
    return pitch_class(a) == pitch_class(b)


def same_notes(a, b):
    """Same notes in the same order, ignoring spelling and case."""
    return len(a) == len(b) and all(same_note(x, y) for x, y in zip(a, b))


def gaps(notes):
    """Semitones between neighbouring notes, always counted upwards: ['C','E','G'] -> [4, 3]."""
    pcs = [pitch_class(n) for n in notes]
    return [(b - a) % 12 for a, b in zip(pcs, pcs[1:])]


def chord_root(name):
    """'F#m7' -> 'F#', 'Bbmaj7' -> 'Bb', 'C' -> 'C'."""
    s = str(name).strip().replace("♯", "#").replace("♭", "b")
    root = s[:1].upper()
    if len(s) > 1 and s[1] in "#b":
        root += s[1]
    pitch_class(root)
    return root


def same_chord(a, b):
    """Same root (any spelling) and the same quality suffix: 'A#m' == 'Bbm', 'Bb' != 'Bbm'."""
    ra, rb = chord_root(a), chord_root(b)
    return same_note(ra, rb) and str(a).strip()[len(ra):] == str(b).strip()[len(rb):]


if __name__ == "__main__":
    assert pitch_class("c#") == pitch_class("Db") == 1 and pitch_class("Cb") == 11 and pitch_class("B#") == 0
    assert gaps(["C", "E", "G"]) == [4, 3] and gaps(["A", "C", "E"]) == [3, 4] and gaps(["G", "C"]) == [5]
    assert same_notes(["Bb", "D", "F"], ["A#", "d", "F"]) and not same_notes(["C", "E"], ["C", "Eb"])
    assert chord_root("F#m7") == "F#" and same_chord("A#m", "Bbm") and not same_chord("Bb", "Bbm")
    print("notes.py self-check passed")
