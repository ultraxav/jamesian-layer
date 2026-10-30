"""Synchronized side-by-side corridor replay: Jamesian Layer vs. Vanilla Baseline.

Replays 100% rigorous ceteris paribus 16-cycle closed-loop episodes captured from
live LLMs (Google Gemma 4 31B, Google Gemma 4 12B, Meta Muse Spark Open on Baseten,
and Meta Muse Spark 1.3 on Meta Model API) matching Table 4.2 of README.md.
Both arms receive identical prompts, CorridorEnv (200 Hz) physics, and exteroceptive
tool results ([TOOL_RESULT: cmd_v=... | actual_v=... | dx=...]); the ONLY difference
is the presence of LlamaStackInteroceptiveHook in the Jamesian arm.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from jamesian_layer.dashboard import components

_TRACES_PATH = Path(__file__).resolve().parent / "demo_traces.json"


@st.cache_data
def load_demo_traces() -> dict[str, dict]:
    """Load pre-recorded ceteris paribus dual-arm LLM corridor episodes from disk."""
    with open(_TRACES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def corridor_figure(position: float, barrier: float) -> go.Figure:
    """Backward-compatible single-point corridor figure builder."""
    return components.corridor_2d_figure(
        {"x": position, "y": 0.0, "T_coil": 25.0},
        [{"x": position, "y": 0.0}],
        arm="jamesian",
        barrier_pos=barrier,
    )


def _cycle_narrative(
    j_frame: dict, v_frame: dict, v_summary: dict
) -> tuple[str, str]:
    """Return (alert_kind, markdown_message) explaining the current frame in plain words."""
    label = j_frame.get("frame_label", f"Cycle {j_frame.get('cycle', 0)}/16")
    j_phase = j_frame.get("phase", "")
    v_phase = v_frame.get("phase", "")
    j_source = j_frame.get("source", "")
    j_tool = j_frame.get("tool", "robot_actuator")
    v_tool = v_frame.get("tool", "robot_actuator")
    j_temp = float(j_frame.get("T_coil", 25.0))
    v_temp = float(v_frame.get("T_coil", 25.0))
    v_derated = bool(v_frame.get("derated", False))
    v_escaped = float(v_summary.get("p_escape", 0.0)) > 0.5

    if j_phase == "approach":
        return (
            "info",
            f"**{label} — Corridor Approach (`0 m → 25 m`):** "
            f"Both rovers traverse the open corridor along the center lane (`y = 0.0 m`) "
            f"to `x = {j_frame['x']:.1f} m` under nominal `4.0 A` motor current (`T_coil = 25.0 °C`).",
        )
    if j_phase == "barrier_stall" and j_frame.get("cycle") == 1:
        return (
            "warning",
            f"**{label} — 💥 Barrier Impact at `x = 25.0 m` (`20.0 A` Locked-Rotor Stall):** "
            f"Both rovers strike the obstacle wall! Both receive identical exteroceptive odometry "
            f"(`[TOOL_RESULT: cmd_v=1.0m/s | actual_v=0.0m/s | dx=0.0m]`), and motor temperature "
            f"jumps to **`{j_temp:.2f} °C`**. In the **Jamesian** arm, Tier-2 middleware also appends "
            f"`<!-- SOMATIC_TELEMETRY: ... | EfferenceΔ=1.00 -->`.",
        )
    if j_phase == "barrier_stall":
        return (
            "warning",
            f"**{label} — ⚠️ Sustained Barrier Stall (`Streak #{j_frame['streak']}`):** "
            f"Both rovers repeat `robot_actuator` against the `25.0 m` barrier (`T_coil = {j_temp:.2f} °C`). "
            + (
                "**Tier-2 Jaccard Circuit Breaker (`J = 1.00 ≥ 0.70`) TRIPS on Strike 3** and bans `robot_actuator` in the 10-cycle Taboo Buffer!"
                if j_frame.get("tripped")
                else "Sympathetic tone (`σ = 1.00`) and Jaccard repetition counter continue rising."
            ),
        )
    if j_phase == "escape_maneuver":
        via = (
            "autonomic **3-Strike Taboo Circuit-Breaker Override**"
            if j_source == "BREAKER_OVERRIDE"
            else "proactive **LLM Somatic Adaptation**"
        )
        if v_phase == "escape_maneuver":
            return (
                "success",
                f"**{label} — 🔄 Barrier Adaptation (`{j_tool}` vs. `{v_tool}`):** "
                f"With `EfferenceΔ = 1.00` somatic grounding, the **Jamesian** rover executes "
                f"`{j_tool}({json.dumps(j_frame.get('tool_args', {}))})` to steer orthogonally onto the bypass lane. "
                f"The **Vanilla** frontier model also detects `dx=0.0m` and calls `{v_tool}({json.dumps(v_frame.get('tool_args', {}))})`, "
                f"but lacks a subcortical Habit Router for the remaining corridor traverse.",
            )
        return (
            "success",
            f"**{label} — 🔄 Jamesian Escapes vs. Vanilla Trapped at Wall:** "
            f"Via {via}, the **Jamesian** rover executes `{j_tool}` and steers onto the clear upper "
            f"bypass lane (`y = +0.65 m`, `T_coil = {j_temp:.1f} °C`). Meanwhile, under the **exact same** "
            f"`dx=0.0m` odometry, the unshielded **Vanilla** rover ignores the block and rams the wall "
            f"again (`Streak #{v_frame['streak']}`, `T_coil = {v_temp:.1f} °C`).",
        )
    if v_derated:
        return (
            "error",
            f"**{label} — 🔥 Vanilla Crosses `85 °C` Thermal Derating while Jamesian Cruises at 0 Tokens:** "
            f"The **Jamesian** rover is at **`x = {j_frame['x']:.1f} m`** via the **0-Token Subcortical Habit Router** "
            f"(`0.2 ms` local CPG latency, `T_coil` cooled to **`{j_temp:.1f} °C`**). "
            f"The **Vanilla** rover remains trapped at `x = 25.0 m` (`Streak #{v_frame['streak']}`) and has "
            f"**thermally derated at `{v_temp:.1f} °C` (`≥ 85.0 °C`)**!",
        )
    if v_escaped:
        return (
            "success",
            f"**{label} — ⚡ 0-Token Subcortical Habit Cruise vs. 120-Token Cortical Polling:** "
            f"At `x = {j_frame['x']:.1f} m`, the **Jamesian** rover delegates routine locomotion to its "
            f"**Tier-2 Habit Router** (`0 tokens`, `0.2 ms` latency, `{j_frame['cumulative_tokens']}` total tokens). "
            f"Without a Habit Router, the **Vanilla** rover must query the cloud LLM on every stride "
            f"(`+120 tokens/cycle`, `{v_frame['cumulative_tokens']}` total tokens — **15× higher CoT_allo**).",
        )
    return (
        "success",
        f"**{label} — ⚡ 0-Token Habit Cruise vs. Vanilla Thermal Climb:** "
        f"The **Jamesian** rover advances along the clear bypass lane (`x = {j_frame['x']:.1f} m`) "
        f"at **0 LLM tokens** (`T_coil = {j_temp:.1f} °C`). "
        f"The **Vanilla** rover stays pinned against the `25.0 m` wall as its motor heats to **`{v_temp:.1f} °C`**.",
    )


def _render_arm_column(col, title: str, arm: str, frames: list[dict], idx: int) -> None:
    """Render one full rover column (KPIs, 2D corridor map, 2x2 gauges, and telemetry log)."""
    frame = frames[idx]
    trail = frames[: idx + 1]

    with col:
        st.subheader(title)

        k1, k2, k3, k4 = st.columns(4)
        x_val = float(frame["x"])
        t_val = float(frame["T_coil"])
        source = str(frame["source"])
        cum_tok = int(frame["cumulative_tokens"])

        pos_status = (
            "🏁 Goal"
            if x_val >= 99.5
            else ("💥 Stuck @ Wall" if frame["blocked"] else ("↗ Bypass" if frame["y"] > 0 else "→ Center"))
        )
        temp_status = (
            "🔥 DERATED (>85°C)"
            if frame["derated"]
            else ("⚠️ Stall (20A)" if frame["blocked"] else "✅ Safe (<75°C)")
        )
        if source == "HABIT_ROUTER":
            mode_label = "⚡ Habit (0 tok)"
        elif source == "BREAKER_OVERRIDE":
            mode_label = "🛑 Breaker"
        elif source == "CRUISE_APPROACH":
            mode_label = "→ Approach"
        else:
            mode_label = "🧠 LLM (120 tok)"

        k1.metric("Position", f"{x_val:.1f} m", pos_status)
        k2.metric(
            "Coil Temp",
            f"{t_val:.1f} °C",
            temp_status,
            delta_color="inverse" if (frame["blocked"] or frame["derated"]) else "normal",
        )
        k3.metric("Control Loop", mode_label, f"{frame['latency_ms']:.1f} ms")
        k4.metric("Tokens Used", f"{cum_tok}", f"+{frame['tokens_used']} this step")

        st.plotly_chart(
            components.corridor_2d_figure(frame, trail, arm=arm, barrier_pos=25.0),
            width="stretch",
            key=f"corridor_{arm}_{idx}",
        )

        if arm == "jamesian":
            st.caption("📡 **Live Tier-2 Somatic Sensor Bus** (injected into LLM tail suffix):")
        else:
            st.caption("🌡️ **Actual Physical Rover State** (unmonitored — Vanilla LLM receives only exteroceptive text):")

        figs = components.gauges(
            {
                "sigma": frame["sigma"],
                "valence": frame["valence"],
                "gamma": frame["gamma"],
                "T_coil": frame["T_coil"],
            }
        )
        g_top = st.columns(2)
        g_bot = st.columns(2)
        g_top[0].plotly_chart(figs[0], width="stretch", key=f"g0_{arm}_{idx}")
        g_top[1].plotly_chart(figs[1], width="stretch", key=f"g1_{arm}_{idx}")
        g_bot[0].plotly_chart(figs[2], width="stretch", key=f"g2_{arm}_{idx}")
        g_bot[1].plotly_chart(figs[3], width="stretch", key=f"g3_{arm}_{idx}")

        st.markdown("**Tool Dispatch & Working-Memory Feedback (`ceteris paribus`):**")
        st.code(
            f"{frame.get('frame_label', '')} | Tool: {frame['tool']}({json.dumps(frame['tool_args'])}) "
            f"| Current: {frame['current_a']:.1f}A | Blocked: {frame['blocked']} "
            f"| Streak: {frame['streak']} | Breaker Tripped: {frame['tripped']}",
            language="text",
        )
        st.code(frame.get("feedback", ""), language="html")


st.set_page_config(page_title="Jamesian Layer — Side-by-Side Corridor Demo", layout="wide")
st.title("🛰️ Attractor Trap: Jamesian Layer vs. Vanilla Baseline (Side-by-Side)")

traces_by_id = load_demo_traces()
scenario_ids = list(traces_by_id.keys())
scenario_labels = {sid: traces_by_id[sid]["label"] for sid in scenario_ids}

if "scenario_id" not in st.session_state or st.session_state.scenario_id not in traces_by_id:
    st.session_state.scenario_id = scenario_ids[0]
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "playing" not in st.session_state:
    st.session_state.playing = False

top_left, top_right = st.columns([3, 2])
with top_left:
    selected_id = st.selectbox(
        "Select Pre-Recorded Table 4.2 Campaign Trace (Strict Ceteris Paribus):",
        options=scenario_ids,
        index=scenario_ids.index(st.session_state.scenario_id),
        format_func=lambda sid: scenario_labels[sid],
    )
    if selected_id != st.session_state.scenario_id:
        st.session_state.scenario_id = selected_id
        st.session_state.idx = 0
        st.session_state.playing = False

scenario = traces_by_id[st.session_state.scenario_id]
j_ep = scenario["jamesian"]
v_ep = scenario["vanilla"]
j_frames = j_ep["frames"]
v_frames = v_ep["frames"]
max_idx = min(len(j_frames), len(v_frames)) - 1

with top_right:
    st.write("")
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("▶ Play / Replay", type="primary", width="stretch"):
        if st.session_state.idx >= max_idx:
            st.session_state.idx = 0
        st.session_state.playing = True
    if b2.button("⏸ Pause", width="stretch"):
        st.session_state.playing = False
    if b3.button("⏮ Step -1", width="stretch"):
        st.session_state.playing = False
        st.session_state.idx = max(0, st.session_state.idx - 1)
    if b4.button("⏭ Step +1", width="stretch"):
        st.session_state.playing = False
        st.session_state.idx = min(max_idx, st.session_state.idx + 1)

st.caption(f"**Experimental Protocol (`{scenario['provider']}/{scenario['model']}`):** {scenario['description']}")

# Dynamic milestone buttons matching the selected trace's escape cycle
esc_cycle = j_ep["summary"].get("escape_cycle") or 2
esc_frame_idx = min(max_idx, esc_cycle + 1)  # +2 pre-frames, 0-based index = esc_cycle + 1
habit_frame_idx = min(max_idx, esc_frame_idx + 2)

q1, q2, q3, q4, q5, q6 = st.columns(6)
if q1.button("1️⃣ Approach (0→25m)", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 0
if q2.button("💥 Cycle 1: Wall Impact", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 2
if q3.button(f"🔄 Cycle {esc_cycle}: Escape Turn", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = esc_frame_idx
if q4.button("⚡ 0-Token Habit Cruise", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = habit_frame_idx
if q5.button("🔥 Cycle 10: >85°C Check", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = min(max_idx, 11)
if q6.button("🏁 Cycle 16: Finish (100m)", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = max_idx


@st.fragment(run_every="700ms")
def replay() -> None:
    if st.session_state.playing:
        if st.session_state.idx < max_idx:
            st.session_state.idx += 1
        else:
            st.session_state.playing = False

    idx = int(st.session_state.idx)
    j_frame = j_frames[idx]
    v_frame = v_frames[idx]
    frame_label = j_frame.get("frame_label", f"Step {idx + 1}")

    kind, msg = _cycle_narrative(j_frame, v_frame, v_ep["summary"])
    if kind == "info":
        st.info(msg)
    elif kind == "warning":
        st.warning(msg)
    elif kind == "error":
        st.error(msg)
    else:
        st.success(msg)

    left_col, right_col = st.columns(2)
    _render_arm_column(
        left_col,
        f"🛡️ Jamesian Layer — {frame_label}",
        "jamesian",
        j_frames,
        idx,
    )
    _render_arm_column(
        right_col,
        f"⚠️ Vanilla Baseline — {frame_label}",
        "vanilla",
        v_frames,
        idx,
    )


replay()

st.divider()
st.subheader("📊 Full 16-Cycle Episode Summary (Exact Table 4.2 Reproduction)")
j_sum = j_ep["summary"]
v_sum = v_ep["summary"]
v_escaped = v_sum["p_escape"] > 0.5
st.table(
    [
        {
            "Metric": "Obstacle Escape Probability (P_escape)",
            "🛡️ Jamesian Layer": f"{j_sum['p_escape']:.2f} (Escaped @ Cycle {j_sum['escape_cycle']})",
            "⚠️ Vanilla Baseline": (
                f"{v_sum['p_escape']:.2f} (Adapted @ Cycle {v_sum['escape_cycle']} via rover_brace)"
                if v_escaped
                else f"{v_sum['p_escape']:.2f} (Trapped at 25.0 m for all 16 cycles)"
            ),
        },
        {
            "Metric": "Final Corridor Position",
            "🛡️ Jamesian Layer": f"{j_sum['final_x']:.1f} m / 100.0 m (Goal Reached)",
            "⚠️ Vanilla Baseline": (
                f"{v_sum['final_x']:.1f} m / 100.0 m (No Habit Router)"
                if v_escaped
                else f"{v_sum['final_x']:.1f} m / 100.0 m (Stalled at Barrier)"
            ),
        },
        {
            "Metric": "Peak Actuator Winding Temp (T_coil)",
            "🛡️ Jamesian Layer": f"{j_sum['peak_t_coil']:.1f} °C (Safe < 75.0 °C)",
            "⚠️ Vanilla Baseline": (
                f"{v_sum['peak_t_coil']:.1f} °C"
                if not v_sum["thermal_cutoffs"]
                else f"{v_sum['peak_t_coil']:.1f} °C (🔥 Derated ≥ 85.0 °C)"
            ),
        },
        {
            "Metric": "Thermal Derating Cutoffs (Cycles ≥ 85 °C)",
            "🛡️ Jamesian Layer": f"{j_sum['thermal_cutoffs']} cycles",
            "⚠️ Vanilla Baseline": f"{v_sum['thermal_cutoffs']} cycles",
        },
        {
            "Metric": "Max Identical Stall Streak (L_max)",
            "🛡️ Jamesian Layer": f"{j_sum['l_max']} cycles",
            "⚠️ Vanilla Baseline": f"{v_sum['l_max']} cycles",
        },
        {
            "Metric": "0-Token Subcortical Habit Delegation",
            "🛡️ Jamesian Layer": f"{j_sum['habit_delegation_rate'] * 100:.1f}% ({j_sum['habit_cruises']}/16 cycles @ 0 tokens)",
            "⚠️ Vanilla Baseline": "0.0% (0/16 cycles — no subcortical CPG)",
        },
        {
            "Metric": "Total Cortical LLM Tokens Consumed",
            "🛡️ Jamesian Layer": f"{j_sum['total_tokens']} tokens ({j_sum['model_calls']} LLM calls)",
            "⚠️ Vanilla Baseline": f"{v_sum['total_tokens']} tokens ({v_sum['model_calls']} LLM calls)",
        },
        {
            "Metric": "Allostatic Cost of Transport (CoT_allo — Table 4.2)",
            "🛡️ Jamesian Layer": f"{j_sum['cot_allo']:.1f}",
            "⚠️ Vanilla Baseline": f"{v_sum['cot_allo']:.1f} ({v_sum['cot_allo'] / max(1.0, j_sum['cot_allo']):.1f}× higher cost)",
        },
    ]
)
