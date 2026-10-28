"""Somatic state vector s(t) = [sigma, V, gamma, T_coil] (spec section 5.1)."""

from dataclasses import dataclass


@dataclass
class BiophysicalState:
    sigma: float = 0.20  # Sympathetic tone [0.0, 1.0]
    valence: float = 0.00  # Affective valence [-1.0, +1.0]
    gamma: float = 0.10  # Somatic strain / muscle tension [0.0, 1.0]
    T_coil: float = 25.0  # Actuator winding temperature (C)
    current: float = 4.0  # Actuator drive current (A)
    rho_tau: float = 0.0  # Generation latency decay ratio (dt_gen / tau_sigma)
    mismatch_delta: float = 0.0  # Latest efference-afferent prediction error
    timestamp_ns: int = 0  # Monotonic timestamp in nanoseconds

    def to_telemetry_dict(self) -> dict:
        return {
            "sigma": round(self.sigma, 2),
            "valence": round(self.valence, 2),
            "gamma": round(self.gamma, 2),
            "T_coil": round(self.T_coil, 1),
            "rho_tau": round(self.rho_tau, 2),
            "mismatch_delta": round(self.mismatch_delta, 2),
        }

    def clamp(self) -> "BiophysicalState":
        """Clamp bounded channels in place; returns self for chaining."""
        self.sigma = min(1.0, max(0.0, self.sigma))
        self.valence = min(1.0, max(-1.0, self.valence))
        self.gamma = min(1.0, max(0.0, self.gamma))
        return self
