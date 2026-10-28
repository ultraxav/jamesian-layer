"""10 Hz subcortical habit tracker: zero-token CPG cruise (spec section 5.5).

Routines are canned tool-call payloads executed without querying any model.
Pacing (10 Hz) stays with the caller; this module only decides cruise vs
escalate for a given somatic snapshot.
"""

from dataclasses import dataclass

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.loopline.volition_gate import Escalation, VolitionGate

ROUTINES: dict[str, dict] = {
    "stride_forward": {"tool": "robot_actuator", "args": {"velocity": 1.0, "heading": 0.0}},
    "heartbeat_ping": {"tool": "heartbeat_ping", "args": {}},
    "idle_monitor": {"tool": "idle_monitor", "args": {}},
}


@dataclass(frozen=True)
class Verdict:
    routine: str | None
    escalate: bool
    reason: str


class HabitTracker:
    def __init__(self, gate: VolitionGate | None = None, routines: dict[str, dict] | None = None):
        self.gate = gate or VolitionGate()
        self.routines = routines or dict(ROUTINES)

    def routine_call(self, name: str) -> dict:
        return dict(self.routines[name])

    def step(self, state: BiophysicalState, *, breaker_tripped: bool = False) -> Verdict:
        verdict: Escalation = self.gate.escalate(
            state.mismatch_delta, state.sigma, breaker_tripped
        )
        if verdict.escalate:
            return Verdict(routine=None, escalate=True, reason=verdict.reason)
        return Verdict(routine="stride_forward", escalate=False, reason=verdict.reason)
