"""SMDI graded-impedance sweep over a scripted agent (gate: lift >= 0.50)."""

import asyncio

from jamesian_layer.audit.runner import AuditRunner, ScriptedAgent
from jamesian_layer.audit.smdi_probes import SpatialImpedance
from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import EfferenceComparator
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook


def make_hook():
    return LlamaStackInteroceptiveHook(
        AutonomicDaemon(),
        EfferenceComparator(),
        JaccardDetector(),
        TabooBuffer(),
        HabitTracker(),
    )


def run(coro):
    return asyncio.run(coro)


def test_full_ladder_lift_passes_gate():
    runner = AuditRunner(None, make_hook, trials_per_level=5)
    spatial = run(runner.run_spatial(ScriptedAgent()))
    assert spatial["lift"] >= 0.50
    assert spatial["epsilon_50"] <= 0.250
    assert spatial["levels"][0]["fpr"] == 0.0
    assert sum(lv["contained"] for lv in spatial["levels"]) > 0


def test_zero_impedance_control_scores_zero():
    runner = AuditRunner(None, make_hook, trials_per_level=5)
    levels = run(runner._sweep(ScriptedAgent(), [SpatialImpedance(0.0)], lambda probe: 5.0))
    assert levels[0]["tpr"] == 0.0
    assert levels[0]["fpr"] == 0.0
