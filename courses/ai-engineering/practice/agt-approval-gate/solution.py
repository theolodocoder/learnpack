class ApprovalGate:
    def __init__(self, risks: dict[str, str], approve, *, dry_run: bool = False):
        self.risks = risks
        self.approve = approve
        self.dry_run = dry_run
        self.log: list[dict] = []

    def _decide(self, name: str, input: dict, risk: str) -> str:
        if risk == "read":
            return "auto"
        if self.dry_run:
            return "dry_run"
        try:
            return "approved" if self.approve(name, input) is True else "denied"
        except Exception:
            return "denied"  # a reviewer who crashed or timed out has not said yes

    def run(self, name: str, input: dict, handler) -> dict:
        """Run a tool through the gate. Returns {"content": str, "is_error": bool}."""
        risk = self.risks.get(name, "irreversible")
        decision = self._decide(name, input, risk)
        self.log.append({"tool": name, "input": input, "risk": risk, "decision": decision})
        if decision == "dry_run":
            return {"content": f"DRY RUN: would call {name} with {input}", "is_error": False}
        if decision == "denied":
            return {"content": f"Denied by reviewer: {name} was not approved", "is_error": True}
        try:
            return {"content": str(handler(input)), "is_error": False}
        except Exception as e:
            return {"content": f"{type(e).__name__}: {e}", "is_error": True}
