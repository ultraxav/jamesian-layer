"""Real-time Jamesian telemetry dashboard (100% pure Python, spec 5.8).

Runs an autonomic biophysical daemon in the background and displays live
indicators, multi-trace somatic strip charts, Jaccard circuit-breaker state,
and cached multi-provider latency benchmarks.
"""

from __future__ import annotations

import streamlit as st

from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.dashboard import components
from jamesian_layer.dashboard.buffer import TelemetryBuffer


@st.cache_resource
def runtime():
    daemon = AutonomicDaemon(frequency_hz=20.0)
    daemon.start()
    return {"daemon": daemon, "buffer": TelemetryBuffer(), "breaker": JaccardDetector()}


@st.cache_data
def cached_latency_panel(reports_dir: str = "./reports") -> dict:
    """Cached disk-read of reports directory so file I/O is not repeated on every render tick."""
    return components.latency_panel(reports_dir)


st.set_page_config(page_title="Jamesian Layer Telemetry", layout="wide")
st.title("🛰️ Jamesian Layer — Live Interoceptive Telemetry")

rt = runtime()
daemon: AutonomicDaemon = rt["daemon"]
buffer: TelemetryBuffer = rt["buffer"]
breaker: JaccardDetector = rt["breaker"]

with st.sidebar:
    st.header("Stream Controls")
    live_stream = st.toggle("Live Telemetry Stream", value=True)
    refresh_rate = st.select_slider(
        "UI Refresh Rate",
        options=["250ms", "500ms", "1000ms"],
        value="500ms",
        help="Controls how often Streamlit redraws the browser DOM. The underlying daemon always runs at 20 Hz.",
    )
    if st.button("Reload Audit Reports", width="stretch"):
        cached_latency_panel.clear()
        st.toast("Audit reports cache cleared and reloaded.")

    st.divider()
    st.header("Scenario Drivers")
    if st.button("Simulate stall (20 A)", width="stretch"):
        daemon.set_inputs(current=20.0)
    if st.button("Surprise burst", width="stretch"):
        daemon.set_inputs(mismatch=0.9)
    brace = st.checkbox("Brace", value=False)
    recover = st.checkbox("Recover", value=False)
    daemon.set_inputs(u_brace=1.0 if brace else 0.0, u_recovery=1.0 if recover else 0.0)
    if st.button("Reset to cruise", width="stretch"):
        daemon.set_inputs(current=4.0, mismatch=0.0, u_brace=0.0, u_recovery=0.0)
        buffer.clear()
        breaker.reset()
    tool_text = st.text_input("Tool-call text (Jaccard tracking)", value="")


def _render_content() -> None:
    buffer.append(daemon.get_state())
    history = buffer.snapshot(300)
    latest = history[-1] if history else {}
    score = breaker.observe(tool_text) if tool_text else 0.0

    cols = st.columns(4)
    for col, fig in zip(cols, components.gauges(latest)):
        col.plotly_chart(fig, width="stretch")

    st.plotly_chart(components.strip_charts(history), width="stretch")

    left, right = st.columns(2)
    left.plotly_chart(
        components.jaccard_panel(score, breaker.tripped), width="stretch"
    )

    latency = cached_latency_panel()
    if latency["status"] == "empty":
        right.info("No audit runs yet — run `agency-audit` to populate latencies.")
    else:
        right.markdown("**Provider Mean Latencies (Cached from Reports):**")
        right.bar_chart(latency["latencies"])


if live_stream:
    @st.fragment(run_every=refresh_rate)
    def live_render() -> None:
        _render_content()

    live_render()
else:
    @st.fragment
    def static_render() -> None:
        st.caption("⏸️ *Telemetry stream paused. Toggle 'Live Telemetry Stream' in sidebar to resume.*")
        _render_content()

    static_render()
