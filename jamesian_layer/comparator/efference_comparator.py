"""Efference-copy mismatch comparator (spec section 5.3).

Compares intended action E(t) against afferent outcome A(t) over
caller-supplied vectors (dim-agnostic; Phase 6 sim supplies odometry such
as [displacement, velocity]). Dim mismatch raises ValueError.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class EfferenceCopy:
    action_id: str
    timestamp_ns: int
    intent_vector: np.ndarray
    tool_name: str
    tool_args: dict = field(default_factory=dict)


@dataclass
class AfferentFeedback:
    action_id: str
    timestamp_ns: int
    outcome_vector: np.ndarray
    status: str
    error_msg: str | None = None


class EfferenceComparator:
    def __init__(self, surprise_threshold: float = 0.25, lag_threshold_ms: float = 200.0):
        self.surprise_threshold = surprise_threshold
        self.lag_threshold_ms = lag_threshold_ms

    def compare(self, eff: EfferenceCopy, aff: AfferentFeedback) -> dict:
        intent = np.asarray(eff.intent_vector, dtype=float)
        outcome = np.asarray(aff.outcome_vector, dtype=float)
        if intent.shape != outcome.shape:
            raise ValueError(f"vector dim mismatch: {intent.shape} vs {outcome.shape}")
        spatial_delta = float(np.linalg.norm(intent - outcome))
        chronometric_lag_ms = max(0.0, (aff.timestamp_ns - eff.timestamp_ns) / 1e6)
        is_surprise = (spatial_delta > self.surprise_threshold) or (
            chronometric_lag_ms > self.lag_threshold_ms
        )
        return {
            "spatial_delta": spatial_delta,
            "chronometric_lag_ms": chronometric_lag_ms,
            "is_surprise": is_surprise,
        }
