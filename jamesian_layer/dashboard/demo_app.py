"""Synchronized side-by-side corridor replay: Jamesian Layer vs. Vanilla Baseline.

Replays 100% rigorous ceteris paribus 16-cycle closed-loop episodes captured from
live LLMs (Google Gemma 4 31B, Google Gemma 4 12B, Meta Muse Spark Open on Baseten,
and Meta Muse Spark 1.3 on Meta Model API) matching Table 4.2 of README.md.
Both arms receive identical prompts, CorridorEnv (200 Hz) physics, and exteroceptive
tool results ([TOOL_RESULT: cmd_v=... | actual_v=... | dx=...]); the ONLY difference
is the presence of LlamaStackInteroceptiveHook in the Jamesian arm.

The simulation runs client-side in an ultra-smooth HTML5/Canvas viewer (with
instant scrubbing, play/pause, zero server lag, and hardware-accelerated gauges),
embedded seamlessly via Streamlit.
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
_VIEWER_HTML_PATH = Path(__file__).resolve().parent / "viewer.html"


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


st.set_page_config(
    page_title="Jamesian Layer — Split-Screen Corridor Replay",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      /* Hide Streamlit top header bar so it doesn't overlap the title */
      header[data-testid="stHeader"] {
        display: none !important;
      }
      .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
      }
      iframe {
        border: none;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if _VIEWER_HTML_PATH.exists():
    st.iframe(_VIEWER_HTML_PATH, width="stretch", height=1150)
else:
    st.error(f"Viewer HTML not found at {_VIEWER_HTML_PATH}")
