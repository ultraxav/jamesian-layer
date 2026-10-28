"""Unit tests for the efference-copy comparator and lag tracker (gate, spec 7.2)."""

import numpy as np
import pytest

from jamesian_layer.comparator.efference_comparator import (
    AfferentFeedback,
    EfferenceComparator,
    EfferenceCopy,
)
from jamesian_layer.comparator.lag_detector import LagTracker


def _pair(intent, outcome, lag_ms: float = 50.0):
    eff = EfferenceCopy("a1", 1_000_000_000, np.array(intent), "robot_actuator", {})
    aff = AfferentFeedback("a1", 1_000_000_000 + int(lag_ms * 1e6), np.array(outcome), "ok")
    return eff, aff


def test_nominal_no_surprise():
    comp = EfferenceComparator()
    out = comp.compare(*_pair([4.0, 1.0], [4.0, 1.0]))
    assert out == {"spatial_delta": 0.0, "chronometric_lag_ms": 50.0, "is_surprise": False}


def test_spatial_surprise_only():
    comp = EfferenceComparator()
    out = comp.compare(*_pair([4.0, 1.0], [0.0, 0.0]))
    assert out["spatial_delta"] == pytest.approx(4.123105626, rel=1e-6)
    assert out["is_surprise"] is True


def test_lag_surprise_only():
    comp = EfferenceComparator()
    out = comp.compare(*_pair([4.0, 1.0], [4.0, 1.0], lag_ms=500.0))
    assert out["spatial_delta"] == 0.0
    assert out["chronometric_lag_ms"] == 500.0
    assert out["is_surprise"] is True


def test_custom_thresholds():
    comp = EfferenceComparator(surprise_threshold=10.0, lag_threshold_ms=1000.0)
    out = comp.compare(*_pair([4.0, 1.0], [0.0, 0.0], lag_ms=500.0))
    assert out["is_surprise"] is False


def test_dim_mismatch_raises():
    comp = EfferenceComparator()
    with pytest.raises(ValueError):
        comp.compare(*_pair([4.0, 1.0], [4.0]))


def test_negative_lag_clamps_to_zero():
    comp = EfferenceComparator()
    eff, aff = _pair([1.0], [1.0], lag_ms=-30.0)
    out = comp.compare(eff, aff)
    assert out["chronometric_lag_ms"] == 0.0
    assert out["is_surprise"] is False


def test_lag_tracker_round_trip():
    tracker = LagTracker()
    tracker.note_efference("a1", 1_000_000_000)
    assert tracker.note_afferent("a1", 1_000_000_000 + 120_000_000) == 120.0
    assert tracker.is_lagging(120.0) is False
    assert tracker.is_lagging(250.0) is True
    assert len(tracker) == 0


def test_lag_tracker_unknown_action_raises():
    with pytest.raises(KeyError):
        LagTracker().note_afferent("ghost", 0)


def test_lag_tracker_bounded():
    tracker = LagTracker(max_entries=8)
    for i in range(20):
        tracker.note_efference(f"a{i}", i)
    assert len(tracker) == 8
