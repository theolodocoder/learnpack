from solution import verse, chorus, bridge
from notes import same_chord


def _match(given, expected):
    return len(given) == len(expected) and all(same_chord(g, e) for g, e in zip(given, expected))


def test_verse_is_one_five_six_four_in_a():
    assert _match(verse, ["A", "E", "F#m", "D"]), \
        "A major is A B C# D E F# G#. 1 = A, 5 = E, 6 = F#m (minor), 4 = D"


def test_chorus_is_four_one_five_six_in_a():
    assert _match(chorus, ["D", "A", "E", "F#m"]), "4 = D, 1 = A, 5 = E, 6 = F#m"


def test_bridge_is_two_five_one_in_a():
    assert _match(bridge, ["Bm", "E", "A"]), "2 = B, which is minor in a major key: Bm. Then 5 = E, 1 = A"
