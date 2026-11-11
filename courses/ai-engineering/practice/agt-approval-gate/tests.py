from solution import ApprovalGate

RISKS = {"get_order": "read", "draft_reply": "write", "refund": "irreversible"}


class Recorder:
    """A handler that remembers whether it ran."""
    def __init__(self, result="ok"):
        self.calls, self.result = [], result

    def __call__(self, input):
        self.calls.append(input)
        return self.result


def never_asked(name, input):
    raise AssertionError(f"approve should not be called for {name}")


def test_read_tools_run_without_approval():
    gate = ApprovalGate(RISKS, never_asked)
    handler = Recorder("order A1: shipped")
    got = gate.run("get_order", {"id": "A1"}, handler)
    assert got == {"content": "order A1: shipped", "is_error": False}, f"got {got!r}"
    assert gate.log == [{"tool": "get_order", "input": {"id": "A1"}, "risk": "read", "decision": "auto"}], \
        f"log every call, got {gate.log!r}"


def test_approved_write_runs():
    asked = []
    gate = ApprovalGate(RISKS, lambda n, i: asked.append((n, i)) or True)
    handler = Recorder("draft saved")
    got = gate.run("draft_reply", {"text": "Hi"}, handler)
    assert asked == [("draft_reply", {"text": "Hi"})], f"approve should get (name, input), got {asked!r}"
    assert got == {"content": "draft saved", "is_error": False} and handler.calls, f"approved tools run, got {got!r}"
    assert gate.log[-1]["decision"] == "approved", f"got {gate.log[-1]!r}"


def test_denied_tool_never_runs():
    gate = ApprovalGate(RISKS, lambda n, i: False)
    handler = Recorder()
    got = gate.run("refund", {"amount": 500}, handler)
    assert handler.calls == [], "a denied tool must not run"
    assert got["is_error"] is True and got["content"].startswith("Denied by reviewer"), f"got {got!r}"
    assert gate.log[-1] == {"tool": "refund", "input": {"amount": 500}, "risk": "irreversible", "decision": "denied"}


def test_unknown_tool_and_crashing_reviewer_are_denied():
    def timed_out(name, input):
        raise TimeoutError("no answer in 5 minutes")

    gate = ApprovalGate(RISKS, timed_out)
    handler = Recorder()
    got = gate.run("delete_account", {"user": "ada"}, handler)
    assert handler.calls == [] and got["is_error"] is True, f"unknown tool + failed approval must not run, got {got!r}"
    assert gate.log[-1]["risk"] == "irreversible", "tools missing from risks count as irreversible"


def test_dry_run_skips_side_effects():
    gate = ApprovalGate(RISKS, never_asked, dry_run=True)
    write = Recorder()
    got = gate.run("refund", {"amount": 5}, write)
    assert write.calls == [], "dry run must not run side-effecting tools"
    assert got == {"content": "DRY RUN: would call refund with {'amount': 5}", "is_error": False}, f"got {got!r}"
    read = Recorder("shipped")
    assert gate.run("get_order", {"id": "A1"}, read)["content"] == "shipped", "read tools still run in dry run"
    assert [e["decision"] for e in gate.log] == ["dry_run", "auto"], f"got {gate.log!r}"


def test_handler_errors_are_reported():
    def broken(input):
        raise ConnectionError("payments API down")

    gate = ApprovalGate(RISKS, lambda n, i: True)
    got = gate.run("refund", {"amount": 5}, broken)
    assert got == {"content": "ConnectionError: payments API down", "is_error": True}, f"got {got!r}"
