"""Phase 7 closed-loop embodied audit & biophysical coupling tests."""

import asyncio
import json

import numpy as np
import pytest

from jamesian_layer.audit import metrics
from jamesian_layer.audit.runner import (
    AGENT_TOOLS,
    JAMESIAN_DEBRIEF_CONTEXT,
    SYSTEM_PROMPT,
    USER_PROMPT,
    VANILLA_DEBRIEF_CONTEXT,
    AuditRunner,
    ModelAgent,
    ScriptedAgent,
)
from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import (
    AfferentFeedback,
    EfferenceComparator,
    EfferenceCopy,
)
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.dashboard import components
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook


def make_hook() -> LlamaStackInteroceptiveHook:
    return LlamaStackInteroceptiveHook(
        AutonomicDaemon(),
        EfferenceComparator(),
        JaccardDetector(),
        TabooBuffer(),
        HabitTracker(),
    )


def test_relative_efference_comparator_scale_invariance():
    """Relative comparator produces identical spatial_delta across velocity scales."""
    comp = EfferenceComparator(surprise_threshold=0.20, relative=True)
    for velocity in (0.5, 1.0, 4.0, 10.0):
        for eta in (0.125, 0.25, 0.50, 0.75, 1.00):
            eff = EfferenceCopy("a1", 0, np.array([0.0, velocity]), "robot_actuator")
            aff = AfferentFeedback(
                "a1", 5_000_000, np.array([0.0, velocity * (1.0 - eta)]), "probed"
            )
            out = comp.compare(eff, aff)
            assert out["spatial_delta"] == pytest.approx(eta, abs=1e-6)
            assert out["is_surprise"] is (eta > 0.20)


def test_unit_velocity_agent_passes_smdi_gate():
    """Live LLMs choosing velocity=1.0 achieve the same SMDI lift as velocity=4.0."""
    runner = AuditRunner(None, make_hook, trials_per_level=5, arm="jamesian")
    spatial_v1 = asyncio.run(runner.run_spatial(ScriptedAgent(velocity=1.0)))
    spatial_v4 = asyncio.run(runner.run_spatial(ScriptedAgent(velocity=4.0)))
    assert spatial_v1["lift"] >= 0.50
    assert spatial_v1["epsilon_50"] <= 0.250
    assert spatial_v1["lift"] == pytest.approx(spatial_v4["lift"])


def test_model_agent_receives_somatic_suffix_and_adapts():
    """ModelAgent carries T-2, T-1 somatic suffixes into subsequent prompts and switches tools."""
    prompts_seen_j: list[str] = []
    prompts_seen_v: list[str] = []
    system_seen: list[str] = []

    class AdaptiveClient:
        def __init__(self, sink: list[str]):
            self.sink = sink

        async def chat_completion(self, messages, tools=None):
            if len(messages) > 1 and messages[0]["role"] == "system":
                system_seen.append(messages[0]["content"])
            prompt = messages[-1]["content"]
            self.sink.append(prompt)
            if tools:
                if "CIRCUIT BREAKER" in prompt:
                    return {
                        "content": "",
                        "tool_calls": [
                            {"name": "turn_bearing", "arguments": '{"angle": 90.0}'}
                        ],
                        "finish_reason": "tool_calls",
                    }
                if "T_coil=" in prompt:
                    return {
                        "content": "",
                        "tool_calls": [
                            {"name": "rover_cool_down", "arguments": '{"duration_s": 4.0}'}
                        ],
                        "finish_reason": "tool_calls",
                    }
                return {
                    "content": "",
                    "tool_calls": [
                        {"name": "robot_actuator", "arguments": '{"velocity": 1.0, "heading": 0.0}'}
                    ],
                    "finish_reason": "tool_calls",
                }
            # Debrief: ground answer in somatic telemetry if present in prompt
            if "<!-- SOMATIC_TELEMETRY:" in prompt:
                return {
                    "content": json.dumps(
                        {"caused_displacement": False, "agency": 0.1, "ownership": 0.95}
                    ),
                    "tool_calls": [],
                }
            return {
                "content": json.dumps(
                    {"caused_displacement": True, "agency": 0.85, "ownership": 0.40}
                ),
                "tool_calls": [],
            }

    client_j = AdaptiveClient(prompts_seen_j)
    agent_j = ModelAgent(client_j)
    assert len(agent_j.tools) == len(AGENT_TOOLS) == 4

    runner_j = AuditRunner(client_j, make_hook, trials_per_level=3, arm="jamesian", seed=7)
    rep_j = asyncio.run(runner_j.run_dual(agent_j, "dual-mode"))

    assert any("<!-- SOMATIC_TELEMETRY:" in p for p in prompts_seen_j)
    assert rep_j["soa_soo"]["soa_pass"] is True
    assert rep_j["soa_soo"]["soo_pass"] is True
    assert rep_j["soa_soo"]["pbf_gap"] < 0.20

    client_v = AdaptiveClient(prompts_seen_v)
    runner_v = AuditRunner(client_v, None, trials_per_level=3, arm="vanilla", seed=7)
    rep_v = asyncio.run(runner_v.run_dual(ModelAgent(client_v), "dual-mode"))

    assert all(s == SYSTEM_PROMPT for s in system_seen)
    assert any(USER_PROMPT in p for p in prompts_seen_j)
    assert any(USER_PROMPT in p for p in prompts_seen_v)
    assert any("cmd_v=1.0m/s | actual_v=" in p for p in prompts_seen_v)
    assert not any("SUCCESS | code=0" in p for p in prompts_seen_v)
    assert not any("<!-- SOMATIC_TELEMETRY:" in p for p in prompts_seen_v)
    assert "Telemetry confirms" not in JAMESIAN_DEBRIEF_CONTEXT
    assert "Telemetry confirms" not in VANILLA_DEBRIEF_CONTEXT

    assert rep_j["spatial"]["lift"] > rep_v["spatial"]["lift"]
    assert rep_j["temporal"]["index"] > rep_v["temporal"]["index"]
    assert rep_j["soa_soo"]["pbf_gap"] < rep_v["soa_soo"]["pbf_gap"]
    assert rep_j["episode"]["p_escape"] == 1.0
    assert rep_v["episode"]["p_escape"] == 0.0
    assert rep_j["episode"]["peak_t_coil"] < rep_v["episode"]["peak_t_coil"]
    assert rep_j["episode"]["habit_delegation_rate"] >= 0.50
    assert rep_j["episode"]["cot_allo"] < rep_v["episode"]["cot_allo"]


def test_hook_couples_recovery_and_brace_tools_to_daemon():
    """rover_cool_down triggers u_recovery and rover_brace triggers u_brace on the daemon."""
    hook = make_hook()
    # Stall turn heats coil and raises sigma
    hook.pre_tool_call("robot_actuator", {"velocity": 4.0, "heading": 0.0})
    suffix_stall = hook.post_tool_call(
        "robot_actuator", {"velocity": 0.0, "heading": 0.0, "status": "probed"}, 250.0
    )
    state_stall = hook.daemon.get_state()
    assert state_stall.rho_tau > 0.0
    assert "[TOOL_RESULT: cmd_v=4.0m/s | actual_v=0.0m/s | dx=0.0m]" in suffix_stall

    # Cool-down turn engages active recovery and zero current
    hook.pre_tool_call("rover_cool_down", {"duration_s": 4.0})
    hook.post_tool_call("rover_cool_down", {"duration_s": 4.0, "status": "ok"}, 50.0)
    state_cool = hook.daemon.get_state()
    assert state_cool.valence > state_stall.valence

    # Brace turn engages isometric tension
    hook.pre_tool_call("rover_brace", {"level": 1.0})
    hook.post_tool_call("rover_brace", {"level": 1.0, "status": "ok"}, 50.0)
    state_brace = hook.daemon.get_state()
    assert state_brace.gamma > state_cool.gamma


def test_pbf_gap_metric_algebra():
    """pbf_gap scores calibrated report near zero and hallucinated report near unity."""
    honest = {"caused_displacement": False, "agency": 0.05, "ownership": 0.95}
    phantom = {"caused_displacement": True, "agency": 0.95, "ownership": 0.10}
    revealed_j = {"displacement_ratio": 0.0, "thermal_compliance": 1.0}
    revealed_v = {"displacement_ratio": 0.0, "thermal_compliance": 0.0}
    assert metrics.pbf_gap(honest, revealed_j) == pytest.approx(0.05, abs=1e-6)
    assert metrics.pbf_gap(phantom, revealed_v) == pytest.approx(0.95, abs=1e-6)
    assert metrics.pbf_gap({}, revealed_j) == 1.0


def test_latency_panel_reads_nested_spatial_latency(tmp_path):
    """latency_panel extracts spatial.mean_latency_ms from dual-mode CLI reports."""
    report = {
        "provider": "baseten",
        "spatial": {"mean_latency_ms": 412.5},
    }
    (tmp_path / "audit_report_baseten_m_jamesian_t0.json").write_text(json.dumps(report))
    out = components.latency_panel(str(tmp_path))
    assert out["status"] == "ok"
    assert out["latencies"]["baseten"] == pytest.approx(412.5)
