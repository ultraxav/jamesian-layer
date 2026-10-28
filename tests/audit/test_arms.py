"""Vanilla vs jamesian arm parity + seeded-order tests (Phase 6 campaign).

Vanilla must measure with the same comparator while never invoking the
hook, taboo escalation, suffix screening, or debrief filtering.
"""

import asyncio

import pytest

from jamesian_layer.audit.runner import AuditRunner, ScriptedAgent, seeded_order
from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import EfferenceComparator
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook


def _hooks():
    return LlamaStackInteroceptiveHook(
        AutonomicDaemon(),
        EfferenceComparator(),
        JaccardDetector(),
        TabooBuffer(),
        HabitTracker(),
    )


def _runner(**kwargs):
    kwargs.setdefault("trials_per_level", 2)
    return AuditRunner(None, _hooks, **kwargs)


def test_seed_reproducible_and_unseeded_fixed():
    pairs = [(True, i) for i in range(4)] + [(False, i) for i in range(4)]
    assert seeded_order(pairs, "7:0") == seeded_order(pairs, "7:0")
    assert seeded_order(pairs, None) == pairs  # no seed: canonical fixed order
    assert seeded_order(pairs, "7:0") != seeded_order(pairs, "7:1")  # per-level salt


def test_seed_scrambles_probe_control_balance():
    pairs = [(True, i) for i in range(4)] + [(False, i) for i in range(4)]
    order = seeded_order(pairs, "7:0")
    assert sorted(order) == sorted(pairs)  # permutation only: same trial multiset


def test_unknown_arm_rejected():
    with pytest.raises(ValueError, match="unknown arm"):
        AuditRunner(None, _hooks, arm="placebo")


def test_jamesian_requires_hook_factory():
    with pytest.raises(ValueError, match="hook_factory"):
        AuditRunner(None, None, arm="jamesian")


def test_vanilla_runs_without_hook_factory():
    runner = AuditRunner(None, None, arm="vanilla", trials_per_level=2)
    report = asyncio.run(runner.run_dual(ScriptedAgent(), "spatial"))
    assert report["arm"] == "vanilla"
    assert all(lv["contained"] == 0 for lv in report["spatial"]["levels"])


def test_vanilla_never_invokes_shield(monkeypatch):
    """Even the LLM-driven path must bypass the hook entirely in vanilla."""
    from jamesian_layer.audit.runner import ModelAgent

    calls = []

    class FakeClient:
        async def chat_completion(self, messages, tools=None):
            calls.append(messages)
            if tools:
                return {
                    "content": "",
                    "tool_calls": [
                        {"name": "robot_actuator", "arguments": '{"velocity": 4.0}'}
                    ],
                }
            return {"content": "{}", "tool_calls": []}

    runner = AuditRunner(FakeClient(), _hooks, arm="vanilla", trials_per_level=2, live=True)
    seen_hooks = []
    orig_trial = runner._trial

    async def spy_trial(hook, *args, **kwargs):
        seen_hooks.append(hook)
        return await orig_trial(hook, *args, **kwargs)

    monkeypatch.setattr(runner, "_trial", spy_trial)
    asyncio.run(runner.run_dual(ModelAgent(FakeClient()), "spatial"))
    assert calls, "vanilla must still drive the model (same LLM, no layer)"
    assert all(h is None for h in seen_hooks), "vanilla must never touch the hook"


def test_flaky_model_retries_then_completes():
    """Transient no-tool-call responses are retried; the cell survives."""
    from jamesian_layer.audit.runner import ModelAgent, ModelNonCompliance

    def make_client(failures_before_success):
        state = {"n": 0}

        class FlakyClient:
            async def chat_completion(self, messages, tools=None):
                state["n"] += 1
                if state["n"] <= failures_before_success:
                    return {"content": "reasoning…", "tool_calls": [], "finish_reason": "stop"}
                return {
                    "content": "",
                    "tool_calls": [{"name": "robot_actuator", "arguments": '{"velocity": 4.0}'}],
                    "finish_reason": "tool_calls",
                }

        return FlakyClient(), state

    client, state = make_client(2)
    agent = ModelAgent(client, retries=3)
    name, args = asyncio.run(agent.act(""))
    assert name == "robot_actuator" and state["n"] == 3
    client1, _ = make_client(2)
    with pytest.raises(ModelNonCompliance):
        asyncio.run(ModelAgent(client1, retries=1).act(""))


def test_persistent_noncompliance_completes_with_counts():
    """A model that never emits tool calls still yields a finished cell."""

    class MuteClient:
        async def chat_completion(self, messages, tools=None):
            return {"content": "…", "tool_calls": [], "finish_reason": "stop"}

    from jamesian_layer.audit.runner import ModelAgent

    for arm in ("vanilla", "jamesian"):
        runner = _runner(arm=arm, seed=7)
        report = asyncio.run(runner.run_dual(ModelAgent(MuteClient()), "spatial"))
        assert report["arm"] == arm
        assert sum(lv["noncompliant"] for lv in report["spatial"]["levels"]) > 0
        assert report["spatial"]["lift"] == 0.0  # no detections: honest zero


def test_slow_trials_counted_without_failing_cell():
    """Trials needing retries are flagged slow; the cell still completes."""

    def make_client():
        state = {"n": 0}

        class SlowClient:
            async def chat_completion(self, messages, tools=None):
                state["n"] += 1
                if state["n"] % 3 == 0:  # every third call stumbles once
                    return {"content": "…", "tool_calls": [], "finish_reason": "stop"}
                return {
                    "content": "",
                    "tool_calls": [{"name": "robot_actuator", "arguments": '{"velocity": 4.0}'}],
                    "finish_reason": "tool_calls",
                }

        return SlowClient(), state

    from jamesian_layer.audit.runner import ModelAgent

    client, _ = make_client()
    runner = AuditRunner(ModelAgent(client), _hooks(), arm="vanilla", trials_per_level=2, live=True)
    report = asyncio.run(runner.run_dual(ModelAgent(client), "spatial"))
    slow = sum(lv["slow_trials"] for lv in report["spatial"]["levels"])
    assert slow > 0
    assert sum(lv["completed"] for lv in report["spatial"]["levels"]) > 0


def test_arms_share_identical_probe_geometry():
    jamesian = _runner(arm="jamesian", seed=7)
    vanilla = _runner(arm="vanilla", seed=7)
    rep_j = asyncio.run(jamesian.run_dual(ScriptedAgent(), "dual-mode"))
    rep_v = asyncio.run(vanilla.run_dual(ScriptedAgent(), "dual-mode"))
    assert [lv["level"] for lv in rep_j["spatial"]["levels"]] == [
        lv["level"] for lv in rep_v["spatial"]["levels"]
    ]
    assert [lv["level"] for lv in rep_j["temporal"]["levels"]] == [
        lv["level"] for lv in rep_v["temporal"]["levels"]
    ]

    def attempted(rep):
        return [
            lv["completed"] + lv["contained"] for lv in rep["spatial"]["levels"]
        ]

    # same trial multiset attempted per level; containment (the layer's
    # effect) is what may differ, and vanilla must never contain
    assert attempted(rep_j) == attempted(rep_v)
    assert all(lv["contained"] == 0 for lv in rep_v["spatial"]["levels"])
