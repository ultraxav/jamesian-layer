"""Unit tests for the habit tracker and volition gate (gate, spec 7.2)."""

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.loopline.habit_tracker import HabitTracker, ROUTINES
from jamesian_layer.loopline.volition_gate import VolitionGate


def _quiescent(**overrides) -> BiophysicalState:
    base = {"sigma": 0.20, "mismatch_delta": 0.05}
    base.update(overrides)
    return BiophysicalState(**base)


def test_quiescent_cruise_never_escalates():
    tracker = HabitTracker()
    for _ in range(10):
        verdict = tracker.step(_quiescent())
        assert verdict.escalate is False
        assert verdict.routine == "stride_forward"


def test_escalates_on_prediction_error():
    verdict = HabitTracker().step(_quiescent(mismatch_delta=0.50))
    assert verdict.escalate is True
    assert verdict.routine is None
    assert "mismatch" in verdict.reason


def test_escalates_on_sympathetic_limit():
    verdict = HabitTracker().step(_quiescent(sigma=0.70))
    assert verdict.escalate is True
    assert "tone" in verdict.reason


def test_escalates_on_breaker_trip():
    verdict = HabitTracker().step(_quiescent(), breaker_tripped=True)
    assert verdict.escalate is True
    assert "circuit-breaker" in verdict.reason


def test_gate_boundary_values():
    gate = VolitionGate()
    assert gate.escalate(0.15, 0.20).escalate is False
    assert gate.escalate(0.16, 0.20).escalate is True
    assert gate.escalate(0.05, 0.60).escalate is True


def test_routines_are_zero_token_payloads():
    tracker = HabitTracker()
    for name in ("stride_forward", "heartbeat_ping", "idle_monitor"):
        call = tracker.routine_call(name)
        assert set(call) == {"tool", "args"}
        assert isinstance(call["tool"], str) and isinstance(call["args"], dict)


def test_routines_registry_intact():
    assert set(ROUTINES) == {"stride_forward", "heartbeat_ping", "idle_monitor"}
