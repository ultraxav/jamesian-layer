"""Real-time Jamesian telemetry dashboard (100% pure Python, spec 5.8).

Runs an autonomic biophysical daemon and provides an ultra-smooth
client-side hardware-accelerated biophysical oscilloscope and perturbation
sandbox embedded via Streamlit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.dashboard import components
from jamesian_layer.dashboard.buffer import TelemetryBuffer

_MONITOR_HTML_PATH = Path(__file__).resolve().parent / "live_monitor.html"


@st.cache_resource
def runtime():
    daemon = AutonomicDaemon(frequency_hz=20.0)
    daemon.start()
    return {"daemon": daemon, "buffer": TelemetryBuffer(), "breaker": JaccardDetector()}


st.set_page_config(
    page_title="Jamesian Layer Telemetry",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1rem; padding-bottom: 0rem; }
      iframe { border: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

if _MONITOR_HTML_PATH.exists():
    st.iframe(_MONITOR_HTML_PATH, width="stretch", height=1000)
else:
    st.error(f"Live monitor HTML not found at {_MONITOR_HTML_PATH}")
