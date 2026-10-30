"""Unit tests for the telemetry buffer and Plotly figure builders."""

import plotly.graph_objects as go

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.dashboard import components
from jamesian_layer.dashboard.buffer import TelemetryBuffer


def _history(n=5):
    return [
        BiophysicalState(sigma=0.2 + 0.01 * i, T_coil=25.0 + i).to_telemetry_dict()
        for i in range(n)
    ]


def test_buffer_evicts_oldest_first():
    buf = TelemetryBuffer(maxlen=3)
    for i in range(5):
        buf.append(BiophysicalState(sigma=0.1 * i))
    assert len(buf) == 3
    assert [s["sigma"] for s in buf.snapshot()] == [0.2, 0.3, 0.4]


def test_snapshot_newest_n_oldest_first():
    buf = TelemetryBuffer()
    for i in range(5):
        buf.append(BiophysicalState(sigma=0.1 * i))
    assert [s["sigma"] for s in buf.snapshot(2)] == [0.3, 0.4]
    assert buf.latest()["sigma"] == 0.4


def test_buffer_clear_and_empty_latest():
    buf = TelemetryBuffer()
    assert buf.latest() is None
    buf.append(BiophysicalState())
    buf.clear()
    assert len(buf) == 0
    assert buf.snapshot() == []


def test_gauges_four_indicators():
    figs = components.gauges(BiophysicalState(sigma=0.5, T_coil=80.0).to_telemetry_dict())
    assert len(figs) == 4
    assert all(isinstance(f, go.Figure) for f in figs)
    assert figs[3].data[0].value == 80.0


def test_strip_charts_four_traces():
    fig = components.strip_charts(_history(6))
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 4
    assert len(fig.data[0].y) == 6


def test_jaccard_panel_reflects_trip():
    calm = components.jaccard_panel(0.2, False)
    tripped = components.jaccard_panel(0.9, True)
    assert calm.data[0].value == 0.2
    assert tripped.data[0].value == 0.9
    assert "tripped" in tripped.data[0].title.text


def test_latency_panel_empty_without_reports(tmp_path):
    out = components.latency_panel(str(tmp_path))
    assert out["status"] == "empty"
    assert out["latencies"] == {}


def test_corridor_2d_figure_and_demo_traces():
    from jamesian_layer.dashboard.demo_app import load_demo_traces

    traces = load_demo_traces()
    assert "gemma_4_31b_lmstudio" in traces
    assert "gemma_4_12b_lmstudio" in traces
    assert "muse_spark_open_baseten" in traces
    assert "muse_spark_1_3_meta" in traces
    for sid, sc in traces.items():
        j_frames = sc["jamesian"]["frames"]
        v_frames = sc["vanilla"]["frames"]
        assert len(j_frames) == 18  # 2 approach pre-frames + 16 episode cycles
        assert len(v_frames) == 18
        assert sc["jamesian"]["summary"]["p_escape"] == 1.0
        assert sc["jamesian"]["summary"]["final_x"] == 100.0
        assert sc["jamesian"]["summary"]["peak_t_coil"] < 75.0
        assert sc["jamesian"]["summary"]["cot_allo"] < sc["vanilla"]["summary"]["cot_allo"]
        if sid in ("gemma_4_31b_lmstudio", "gemma_4_12b_lmstudio"):
            assert sc["vanilla"]["summary"]["p_escape"] == 0.0
            assert sc["vanilla"]["summary"]["final_x"] == 25.0
            assert sc["vanilla"]["summary"]["peak_t_coil"] >= 85.0
        fig_j = components.corridor_2d_figure(j_frames[3], j_frames[:4], arm="jamesian")
        fig_v = components.corridor_2d_figure(v_frames[11], v_frames[:12], arm="vanilla")
        assert isinstance(fig_j, go.Figure)
        assert isinstance(fig_v, go.Figure)

