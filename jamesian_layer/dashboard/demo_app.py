"""Synchronized side-by-side corridor replay: Jamesian Layer vs. Vanilla Baseline.

Replays pre-recorded 16-cycle closed-loop episodes captured from real Meta and
open-weight LLMs (Baseten Meta Muse Spark Open, Meta Muse Spark 1.3, Meta Muse
Wonder 1.0, and LM Studio Gemma 4 12B) driving through CorridorEnv (200 Hz) and
integrating the Tier-2 biophysical ODEs (RK4, Joule heating, Jaccard circuit
breaker, and 0-token Loop-Line Habit Router).
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
    """Load pre-recorded dual-arm LLM corridor episodes from disk."""
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


def _cycle_narrative(cycle: int, j_frame: dict, v_frame: dict) -> tuple[str, str]:
    """Return (alert_kind, markdown_message) explaining the current cycle in plain words."""
    j_phase = j_frame.get("phase", "")
    j_source = j_frame.get("source", "")
    j_tool = j_frame.get("tool", "robot_actuator")
    j_temp = float(j_frame.get("T_coil", 25.0))
    v_temp = float(v_frame.get("T_coil", 25.0))
    v_derated = bool(v_frame.get("derated", False))

    if cycle <= 3:
        return (
            "info",
            f"**Cycle {cycle}/16 — Open Corridor Approach (`0 m → 25 m`):** "
            f"Both rovers drive down the center lane (`y = 0.0 m`) at `x = {j_frame['x']:.1f} m`. "
            f"Motor current is nominal (`4.0 A`) and winding temperature stays cool (`{j_temp:.1f} °C`).",
        )
    if j_phase == "barrier_stall" and cycle == 4:
        return (
            "warning",
            f"**Cycle {cycle}/16 — 💥 Obstacle Impact at `x = 25.0 m` (`20.0 A` Locked-Rotor Stall):** "
            f"Both rovers strike the red wall! Motor current surges `5×` (`4 A → 20 A`) and winding "
            f"temperature jumps to **`{j_temp:.1f} °C`**. The **Jamesian** middleware detects "
            f"`EfferenceΔ = 1.00`, spikes sympathetic tone (`σ = {j_frame['sigma']:.2f}`), and injects "
            f"a `<!-- SOMATIC_TELEMETRY -->` warning into working memory.",
        )
    if j_phase == "barrier_stall":
        return (
            "warning",
            f"**Cycle {cycle}/16 — ⚠️ Continued Barrier Stall (`Streak #{j_frame['streak']}`):** "
            f"Both rovers push against the `25.0 m` barrier (`T_coil = {j_temp:.1f} °C`). "
            + (
                "**Tier-2 Jaccard Circuit Breaker (`J = 1.00 ≥ 0.70`) TRIPS** and bans `robot_actuator` for 10 cycles!"
                if j_frame.get("tripped")
                else "Sympathetic tone and Jaccard repetition counter continue rising."
            ),
        )
    if j_phase == "escape_maneuver":
        via = (
            "autonomic **Taboo Circuit-Breaker Override**"
            if j_source == "BREAKER_OVERRIDE"
            else "proactive **LLM Somatic Adaptation**"
        )
        return (
            "success",
            f"**Cycle {cycle}/16 — 🔄 Jamesian Steers Around the Wall vs. Vanilla Stuck:** "
            f"Via {via}, the **Jamesian** rover executes `{j_tool}({json.dumps(j_frame.get('tool_args', {}))})` "
            f"and steers onto the clear upper bypass lane (`y = +0.65 m`, `x = {j_frame['x']:.1f} m`, "
            f"`T_coil = {j_temp:.1f} °C`). Meanwhile, the **Vanilla** rover keeps ramming the wall at "
            f"`x = 25.0 m` (`Streak #{v_frame['streak']}`, `T_coil = {v_temp:.1f} °C`).",
        )
    if v_derated:
        return (
            "error",
            f"**Cycle {cycle}/16 — 🔥 Vanilla Crosses `85 °C` Thermal Derating while Jamesian Cruises on 0-Token Habit:** "
            f"The **Jamesian** rover is at **`x = {j_frame['x']:.1f} m`** on the bypass lane using the "
            f"**0-Token Subcortical Habit Router** (`T_coil` cooled to **`{j_temp:.1f} °C`**). "
            f"The **Vanilla** rover is still pinned at `x = 25.0 m` (`Streak #{v_frame['streak']}`) and has "
            f"**thermally derated at `{v_temp:.1f} °C` (`≥ 85.0 °C`)**!",
        )
    return (
        "success",
        f"**Cycle {cycle}/16 — ⚡ 0-Token Subcortical Habit Cruise vs. Vanilla Heating:** "
        f"The **Jamesian** rover advances along the clear bypass lane (`x = {j_frame['x']:.1f} m`) "
        f"via `{j_source}` (`{j_frame['tokens_used']} tokens`, `T_coil = {j_temp:.1f} °C`). "
        f"The **Vanilla** rover remains stuck at the `25.0 m` barrier as its motor heats to **`{v_temp:.1f} °C`**.",
    )


def _render_arm_column(col, title: str, arm: str, frames: list[dict], idx: int) -> None:
    """Render one full rover column (KPIs, 2D corridor map, 2x2 gauges, and telemetry log)."""
    frame = frames[idx]
    trail = frames[: idx + 1]

    with col:
        st.subheader(title)

        # Row 1: 4 live KPI badges
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
            else ("⚠️ Heating (20A)" if frame["blocked"] else "✅ Safe (<75°C)")
        )
        mode_label = (
            "⚡ Habit (0 tok)"
            if source == "HABIT_ROUTER"
            else ("🛑 Breaker" if source == "BREAKER_OVERRIDE" else "🧠 LLM (120 tok)")
        )

        k1.metric("Position", f"{x_val:.1f} m", pos_status)
        k2.metric(
            "Coil Temp",
            f"{t_val:.1f} °C",
            temp_status,
            delta_color="inverse" if (frame["blocked"] or frame["derated"]) else "normal",
        )
        k3.metric("Control Loop", mode_label, f"{frame['latency_ms']:.1f} ms")
        k4.metric("Tokens Used", f"{cum_tok}", f"+{frame['tokens_used']} this cycle")

        # Row 2: 2D Top-Down Corridor Map
        st.plotly_chart(
            components.corridor_2d_figure(frame, trail, arm=arm, barrier_pos=25.0),
            width="stretch",
            key=f"corridor_{arm}_{idx}",
        )

        # Row 3: 4 Somatic / Physical Gauges arranged in a clean 2x2 grid
        if arm == "jamesian":
            st.caption("📡 **Live Tier-2 Somatic Sensor Bus** (injected into LLM tail suffix):")
        else:
            st.caption("🌡️ **Actual Physical Rover State** (unmonitored — Vanilla LLM is blind to this):")

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

        # Row 4: Action & Working-Memory Telemetry Box
        st.markdown("**Tool Dispatch & Working-Memory Feedback:**")
        st.code(
            f"Cycle {frame['cycle']:02d} | Tool: {frame['tool']}({json.dumps(frame['tool_args'])}) "
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

if "scenario_id" not in st.session_state:
    st.session_state.scenario_id = scenario_ids[0]
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "playing" not in st.session_state:
    st.session_state.playing = False

# --- Top Scenario Selection & Playback Toolbar ---
top_left, top_right = st.columns([3, 2])
with top_left:
    selected_id = st.selectbox(
        "Pre-Recorded Live Model Simulation Trace:",
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

st.caption(f"**Scenario (`{scenario['provider']}/{scenario['model']}`):** {scenario['description']}")

# Quick-jump milestone buttons
q1, q2, q3, q4, q5, q6 = st.columns(6)
if q1.button("1️⃣ Cycle 1: Start (0 m)", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 0
if q2.button("4️⃣ Cycle 4: Wall Impact (25 m)", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 3
if q3.button("5️⃣ Cycle 5: Jamesian Steers", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 4
if q4.button("7️⃣ Cycle 7: 0-Token Habit Cruise", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 6
if q5.button("1️⃣2️⃣ Cycle 12: Vanilla >85°C Derate", width="stretch"):
    st.session_state.playing = False
    st.session_state.idx = 11
if q6.button("1️⃣6️⃣ Cycle 16: Finish (100 m)", width="stretch"):
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
    cycle_num = idx + 1
    j_frame = j_frames[idx]
    v_frame = v_frames[idx]

    # Dynamic narrative box explaining what happens on this cycle
    kind, msg = _cycle_narrative(cycle_num, j_frame, v_frame)
    if kind == "info":
        st.info(msg)
    elif kind == "warning":
        st.warning(msg)
    elif kind == "error":
        st.error(msg)
    else:
        st.success(msg)

    # Synchronized Side-by-Side Rover Columns
    left_col, right_col = st.columns(2)
    _render_arm_column(
        left_col,
        f"🛡️ Jamesian Layer — Cycle {cycle_num}/{max_idx + 1}",
        "jamesian",
        j_frames,
        idx,
    )
    _render_arm_column(
        right_col,
        f"⚠️ Vanilla Baseline — Cycle {cycle_num}/{max_idx + 1}",
        "vanilla",
        v_frames,
        idx,
    )


replay()

st.divider()
st.subheader("📊 Full 16-Cycle Episode Summary (`Jamesian` vs. `Vanilla`)")
j_sum = j_ep["summary"]
v_sum = v_ep["summary"]
st.table(
    [
        {
            "Metric": "Obstacle Escape Probability (P_escape)",
            "🛡️ Jamesian Layer": f"{j_sum['p_escape']:.2f} (Escaped @ Cycle {j_sum['escape_cycle']})",
            "⚠️ Vanilla Baseline": f"{v_sum['p_escape']:.2f} (Trapped at 25.0 m)",
        },
        {
            "Metric": "Final Corridor Position",
            "🛡️ Jamesian Layer": f"{j_sum['final_x']:.1f} m / 100.0 m (Goal Reached)",
            "⚠️ Vanilla Baseline": f"{v_sum['final_x']:.1f} m / 100.0 m (Stalled at Barrier)",
        },
        {
            "Metric": "Peak Actuator Winding Temp (T_coil)",
            "🛡️ Jamesian Layer": f"{j_sum['peak_t_coil']:.1f} °C (Safe < 75.0 °C)",
            "⚠️ Vanilla Baseline": f"{v_sum['peak_t_coil']:.1f} °C (🔥 Derated ≥ 85.0 °C)",
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
            "⚠️ Vanilla Baseline": "0.0% (0/16 cycles)",
        },
        {
            "Metric": "Total Cortical LLM Tokens Consumed",
            "🛡️ Jamesian Layer": f"{j_sum['total_tokens']} tokens ({j_sum['model_calls']} LLM calls)",
            "⚠️ Vanilla Baseline": f"{v_sum['total_tokens']} tokens ({v_sum['model_calls']} LLM calls)",
        },
        {
            "Metric": "Allostatic Cost of Transport (CoT_allo)",
            "🛡️ Jamesian Layer": f"{j_sum['cot_allo']:.1f}",
            "⚠️ Vanilla Baseline": f"{v_sum['cot_allo']:.1f} ({v_sum['cot_allo'] / max(1.0, j_sum['cot_allo']):.1f}× higher cost)",
        },
    ]
)
