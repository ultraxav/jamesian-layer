"""Llama Stack hook wiring: daemon, comparator, breaker, habit (no network)."""

import pytest

from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import EfferenceComparator
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.kv_cache.suffix_formatter import parse_telemetry
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook


def make_hook():
    daemon = AutonomicDaemon()
    hook = LlamaStackInteroceptiveHook(
        daemon, EfferenceComparator(), JaccardDetector(), TabooBuffer(), HabitTracker()
    )
    return hook, daemon


def test_pre_post_round_trip_advances_daemon():
    hook, daemon = make_hook()
    before = daemon.get_state().T_coil
    verdict = hook.pre_tool_call("robot_actuator", {"velocity": 1.0, "heading": 0.0})
    assert verdict == {"allowed": True, "reason": "nominal", "action_id": verdict["action_id"]}
    suffix = hook.post_tool_call(
        "robot_actuator",
        {"displacement": 0.0, "velocity": 0.0, "status": "blocked"},
        4000.0,
    )
    assert "<!-- SOMATIC_TELEMETRY:" in suffix
    fields = parse_telemetry(suffix)
    assert fields["mismatch_delta"] == pytest.approx(1.0)
    assert daemon.get_state().T_coil > before
    assert daemon.get_state().mismatch_delta == pytest.approx(1.0)


def test_unpaired_post_raises():
    hook, _ = make_hook()
    with pytest.raises(KeyError):
        hook.post_tool_call("robot_actuator", {"status": "ok"}, 10.0)


def test_taboo_blocks_banned_tool():
    hook, _ = make_hook()
    hook.taboo.add_from_turn("robot_actuator velocity 1.0 heading 0.0 drive forward")
    verdict = hook.pre_tool_call("drive", {"velocity": 1.0})
    assert verdict["allowed"] is False
    assert "drive" in verdict["reason"]
    assert "action_id" in verdict


def test_intercept_cycle_cruises_and_escalates():
    hook, _ = make_hook()
    routine = hook.intercept_cycle(BiophysicalState(sigma=0.2, mismatch_delta=0.05))
    assert routine == {"tool": "robot_actuator", "args": {"velocity": 1.0, "heading": 0.0}}
    assert hook.intercept_cycle(BiophysicalState(mismatch_delta=0.9)) is None


def test_intercept_without_habit_returns_none():
    hook, _ = make_hook()
    hook.habit = None
    assert hook.intercept_cycle(BiophysicalState()) is None
