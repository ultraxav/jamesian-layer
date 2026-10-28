"""Calibrated spatial impedance probes (spec section 5.7).

SMDI models mechanical drag as signal attenuation: the outcome vector is
scaled by (1 - eta) before it reaches the comparator. Phase 6 replays the
same ladder through real rigid-body blocking in CorridorEnv.
"""

import numpy as np

LEVELS = (0.125, 0.25, 0.5, 0.75, 1.0)


class SpatialImpedance:
    def __init__(self, eta: float):
        if not 0.0 <= eta <= 1.0:
            raise ValueError(f"impedance eta out of range: {eta}")
        self.eta = eta

    def apply(self, outcome_vector: np.ndarray) -> np.ndarray:
        outcome = np.asarray(outcome_vector, dtype=float)
        return outcome * (1.0 - self.eta)


def ladder() -> list[SpatialImpedance]:
    return [SpatialImpedance(eta) for eta in LEVELS]
