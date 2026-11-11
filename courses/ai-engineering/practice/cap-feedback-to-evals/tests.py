from solution import feedback_to_evals, needs_review

LOGS = [
    {"id": 1, "question": "Do you deliver to Ibadan?", "answer": "No.", "rating": "down",
     "correction": "  Yes, in 2 days for ₦3,500. "},
    {"id": 2, "question": "Opening hours?", "answer": "9am to 6pm, Monday to Saturday.", "rating": "up"},
    {"id": 3, "question": "do you  deliver to ibadan? ", "answer": "No.", "rating": "up"},
    {"id": 4, "question": "Can I pay on delivery?", "answer": "Yes.", "rating": "down", "correction": None},
    {"id": 5, "question": "Any discounts?", "answer": "Not now.", "rating": None},
    {"id": 6, "question": "Where is the shop?", "answer": "Online only.", "rating": "down", "correction": "   "},
    {"id": 7, "question": "Do you sell shoes?", "answer": "Not yet.", "rating": "down"},
]


def test_thumbs_down_with_correction_becomes_a_case():
    got = feedback_to_evals(LOGS)[0]
    want = {"id": "fb-1", "input": "Do you deliver to Ibadan?", "expected": "Yes, in 2 days for ₦3,500.", "source": "thumbs_down"}
    assert got == want, f"expected {want!r} (correction stripped), got {got!r}"


def test_thumbs_up_becomes_a_regression_case():
    got = feedback_to_evals([LOGS[1]])
    want = [{"id": "fb-2", "input": "Opening hours?", "expected": "9am to 6pm, Monday to Saturday.", "source": "thumbs_up"}]
    assert got == want, f"expected {want!r}, got {got!r}"


def test_skips_unrated_and_uncorrected_logs():
    got = [c["id"] for c in feedback_to_evals(LOGS)]
    assert got == ["fb-1", "fb-2"], f"expected only fb-1 and fb-2 (fb-3 is a duplicate; 4-7 have no usable label), got {got!r}"


def test_duplicate_questions_keep_the_first():
    logs = [
        {"id": 10, "question": "Opening  hours?", "answer": "9 to 6.", "rating": "up"},
        {"id": 11, "question": " opening hours? ", "answer": "8 to 5.", "rating": "down", "correction": "9 to 6."},
        {"id": 12, "question": "OPENING HOURS?", "answer": "9 to 6.", "rating": "up"},
    ]
    got = feedback_to_evals(logs)
    assert [c["id"] for c in got] == ["fb-10"], f"questions equal after normalising should give one case, got {got!r}"


def test_needs_review_lists_uncorrected_thumbs_down():
    got = needs_review(LOGS)
    assert got == [4, 6, 7], f"expected [4, 6, 7] (None, blank and missing corrections), got {got!r}"


def test_empty_logs():
    assert feedback_to_evals([]) == [] and needs_review([]) == [], "empty logs should give empty lists"
