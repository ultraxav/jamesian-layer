"""Surprise-driven escalation verdict (spec section 5.5)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Escalation:
    escalate: bool
    reason: str


class VolitionGate:
    def __init__(self, habit_threshold: float = 0.15, sigma_limit: float = 0.60):
        self.habit_threshold = habit_threshold
        self.sigma_limit = sigma_limit

    def escalate(self, mismatch: float, sigma: float, breaker_tripped: bool = False) -> Escalation:
        if breaker_tripped:
            return Escalation(True, "circuit-breaker tripped")
        if mismatch > self.habit_threshold:
            return Escalation(True, f"mismatch {mismatch:.2f} exceeds {self.habit_threshold:.2f}")
        if sigma >= self.sigma_limit:
            return Escalation(True, f"sympathetic tone {sigma:.2f} at limit {self.sigma_limit:.2f}")
        return Escalation(False, "nominal cruise")
