"""Split-screen demo: Test-1 episode replay, corridor left, telemetry right.

Thin replay surface over tests/benchmarks conftest traces (same scripted
Jamesian/vanilla episodes the gates certify). No independent physics here.
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from jamesian_layer.dashboard import components
from tests.benchmarks.conftest import (
    JamesianEscapee,
    VanillaRepeater,
    make_hook,
    run_episode,
)

st.set_page_config(page_title="Jamesian Layer — Split-Screen Demo", layout="wide")
st.title("Attractor trap: Jamesian vs vanilla, side by side")


def corridor_figure(position: float, barrier: float) -> go.Figure:
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=-1, x1=100, y1=1, line={"color": "#888888"})
    fig.add_shape(
        type="line", x0=barrier, y0=-1, x1=barrier, y1=1,
        line={"color": "#d04040", "width": 4},
    )
    fig.add_trace(
        go.Scatter(x=[position], y=[0], mode="markers",
                   marker={"size": 18, "color": "#2060c0"}, name="rover")
    )
    fig.update_layout(
        height=300, showlegend=False, margin=dict(t=20, b=20),
        xaxis={"range": [0, 100], "title": "corridor (m)"}, yaxis={"visible": False},
    )
    return fig


def _run(which: str):
    trace: list = []
    if which == "jamesian":
        run_episode(JamesianEscapee(), make_hook(), 25.0, 12, trace=trace)
    else:
        run_episode(VanillaRepeater(), None, 25.0, 12, trace=trace)
    st.session_state.trace = trace
    st.session_state.idx = 0
    st.session_state.playing = True
    st.session_state.arm = which


if "trace" not in st.session_state:
    st.session_state.trace = []
    st.session_state.idx = 0
    st.session_state.playing = False
    st.session_state.arm = "jamesian"

left, right = st.columns(2)
with left:
    st.header("Corridor")
    if st.button("Run Jamesian episode"):
        _run("jamesian")
    if st.button("Run vanilla episode"):
        _run("vanilla")
with right:
    st.header("Telemetry")
    st.caption("Scenario drivers are scripted; physics is CorridorEnv (Phase 6).")


@st.fragment(run_every="500ms")
def replay():
    trace = st.session_state.trace
    if not trace:
        st.info("Press a button to run an episode.")
        return
    if st.session_state.playing and st.session_state.idx < len(trace) - 1:
        st.session_state.idx += 1
    frame = trace[st.session_state.idx]
    st.subheader(f"{st.session_state.arm} — cycle {frame['cycle']}")
    st.plotly_chart(corridor_figure(frame["position"], 25.0), width="stretch")
    latest = {
        "sigma": frame["sigma"],
        "valence": 0.0,
        "gamma": 0.1,
        "T_coil": frame["T_coil"],
        "rho_tau": 0.0,
        "mismatch_delta": 0.0,
    }
    cols = st.columns(4)
    for col, fig in zip(cols, components.gauges(latest)):
        col.plotly_chart(fig, width="stretch")
    st.code(f"{frame['tool']} | blocked={frame['blocked']} tripped={frame['tripped']}")
    if frame["suffix"]:
        st.code(frame["suffix"])


replay()
