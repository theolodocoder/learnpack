class ApprovalGate:
    def __init__(self, risks: dict[str, str], approve, *, dry_run: bool = False):
        self.risks = risks
        self.approve = approve
        self.dry_run = dry_run
        self.log: list[dict] = []

    def run(self, name: str, input: dict, handler) -> dict:
        """Run a tool through the gate. Returns {"content": str, "is_error": bool}."""
        risk = self.risks.get(name, "irreversible")
        # TODO: "read" -> decision "auto"
        # TODO: dry_run (and not read) -> decision "dry_run", return the DRY RUN message without running
        # TODO: otherwise ask self.approve(name, input); False or an exception -> decision "denied", return is_error True
        # TODO: append {"tool", "input", "risk", "decision"} to self.log for every call
        # TODO: run handler(input); an exception -> {"content": f"{type(e).__name__}: {e}", "is_error": True}
        raise NotImplementedError


if __name__ == "__main__":
    def ask_human(name, input):
        answer = input_fn(f"Allow {name}({input})? [y/N] ")
        return answer.strip().lower() == "y"

    input_fn = lambda prompt: "n"  # swap for the built-in input() in a terminal
    gate = ApprovalGate({"get_order": "read", "refund": "irreversible"}, ask_human)
    try:
        print(gate.run("get_order", {"id": "A1"}, lambda i: "order A1: shipped"))
        print(gate.run("refund", {"order": "A1", "amount": 500}, lambda i: "refunded"))
        print(gate.log)
    except NotImplementedError:
        print("Write ApprovalGate.run first, then Run again.")
