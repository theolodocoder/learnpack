import time

from solution import timer


def test_yields_dict_with_label_and_no_time_yet():
    with timer("step") as t:
        inside = dict(t)
    want = {"label": "step", "seconds": None}
    assert inside == want, f"inside the block expected {want!r}, got {inside!r}"


def test_records_elapsed_seconds():
    with timer("sleep") as t:
        time.sleep(0.05)
    s = t["seconds"]
    assert isinstance(s, float) and 0.04 <= s < 1, f"expected about 0.05 seconds, got {s!r}"


def test_appends_to_log_when_given():
    log = []
    with timer("a", log):
        pass
    with timer("b", log):
        pass
    labels = [entry["label"] for entry in log]
    assert labels == ["a", "b"], f"expected log labels ['a', 'b'], got {labels!r}"


def test_records_time_and_reraises_when_block_fails():
    log = []
    try:
        with timer("boom", log) as t:
            raise RuntimeError("model call failed")
    except RuntimeError:
        pass
    else:
        raise AssertionError("the RuntimeError should propagate out of the with-block")
    assert t["seconds"] is not None, "seconds should be set even when the block raises"
    assert log == [t], f"the result should be logged even when the block raises, got {log!r}"
