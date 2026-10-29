"""Real-time Jamesian telemetry dashboard (100% pure Python, spec 5.8)."""

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


st.set_page_config(page_title="Jamesian Layer Telemetry", layout="wide")
st.title("Jamesian Layer — live interoceptive telemetry")

rt = runtime()
daemon: AutonomicDaemon = rt["daemon"]
buffer: TelemetryBuffer = rt["buffer"]
breaker: JaccardDetector = rt["breaker"]

with st.sidebar:
    st.header("Scenario drivers")
    if st.button("Simulate stall (20 A)"):
        daemon.set_inputs(current=20.0)
    if st.button("Surprise burst"):
        daemon.set_inputs(mismatch=0.9)
    brace = st.checkbox("Brace", value=False)
    recover = st.checkbox("Recover", value=False)
    daemon.set_inputs(u_brace=1.0 if brace else 0.0, u_recovery=1.0 if recover else 0.0)
    if st.button("Reset to cruise"):
        daemon.set_inputs(current=4.0, mismatch=0.0, u_brace=0.0, u_recovery=0.0)
        buffer.clear()
        breaker.reset()
    tool_text = st.text_input("Tool-call text (Jaccard tracking)", value="")


@st.fragment(run_every="100ms")
def render():
    buffer.append(daemon.get_state())
    history = buffer.snapshot(300)
    latest = history[-1] if history else {}
    if tool_text:
        score = breaker.observe(tool_text)
    else:
        score = 0.0

    cols = st.columns(4)
    for col, fig in zip(cols, components.gauges(latest)):
        col.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(components.strip_charts(history), use_container_width=True)
    left, right = st.columns(2)
    left.plotly_chart(
        components.jaccard_panel(score, breaker.tripped), use_container_width=True
    )
    latency = components.latency_panel()
    if latency["status"] == "empty":
        right.info("No audit runs yet — run `agency-audit` to populate latencies.")
    else:
        right.bar_chart(latency["latencies"])


render()
