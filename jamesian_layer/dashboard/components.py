"""Pure Plotly figure builders (no Streamlit imports): gauges, strips, panels."""

import glob
import json
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def gauges(latest: dict) -> list[go.Figure]:
    """Four indicator gauges for the latest somatic snapshot."""
    specs = [
        ("sympathetic tone", latest.get("sigma", 0.0), 0.0, 1.0, None),
        ("valence", latest.get("valence", 0.0), -1.0, 1.0, None),
        ("muscle tension", latest.get("gamma", 0.0), 0.0, 1.0, None),
        (
            "coil temp (C)",
            latest.get("T_coil", 25.0),
            25.0,
            100.0,
            [
                {"range": [25.0, 75.0], "color": "#e8e8e8"},
                {"range": [75.0, 85.0], "color": "#f0c040"},
                {"range": [85.0, 100.0], "color": "#d04040"},
            ],
        ),
    ]
    figures = []
    for title, value, lo, hi, steps in specs:
        gauge: dict = {"axis": {"range": [lo, hi]}}
        if steps is not None:
            gauge["steps"] = steps
            gauge["threshold"] = {
                "line": {"color": "#d04040", "width": 3},
                "thickness": 0.8,
                "value": 85.0,
            }
        figures.append(
            go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=value,
                    title={"text": title},
                    gauge=gauge,
                )
            )
        )
    return figures


def strip_charts(history: list[dict]) -> go.Figure:
    """Time-series strips for sigma, valence, gamma, and coil temperature."""
    keys = ["sigma", "valence", "gamma", "T_coil"]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=keys)
    for i, key in enumerate(keys, start=1):
        fig.add_trace(
            go.Scatter(
                y=[s.get(key, 0.0) for s in history],
                mode="lines",
                name=key,
            ),
            row=i,
            col=1,
        )
    fig.update_layout(height=600, showlegend=False, margin=dict(t=40, b=20))
    return fig


def jaccard_panel(score: float, tripped: bool) -> go.Figure:
    """Repetition index gauge plus breaker state."""
    return go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Jaccard repetition (tripped)" if tripped else "Jaccard repetition"},
            gauge={
                "axis": {"range": [0.0, 1.0]},
                "steps": [
                    {"range": [0.0, 0.7], "color": "#e8e8e8"},
                    {"range": [0.7, 1.0], "color": "#d04040"},
                ],
                "threshold": {"line": {"color": "#d04040", "width": 3}, "value": 0.7},
            },
        )
    )


def latency_panel(reports_dir: str = "./reports") -> dict:
    """Per-provider latencies from audit reports, or an explicit empty state."""
    latencies: dict[str, float] = {}
    paths = sorted(glob.glob(os.path.join(reports_dir, "audit_report_*.json")))
    if not paths and reports_dir == "./reports":
        paths = sorted(glob.glob(os.path.join("./documents", "audit_report_*.json")))
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                report = json.load(fh)
        except (OSError, ValueError):
            continue
        provider = report.get("provider", os.path.basename(path))
        top_lat = report.get("mean_latency_ms")
        spatial_lat = (report.get("spatial") or {}).get("mean_latency_ms")
        val = top_lat if isinstance(top_lat, (int, float)) else (spatial_lat or 0.0)
        latencies[str(provider)] = float(val)
    if not latencies:
        return {"status": "empty", "message": "no audit runs yet", "latencies": {}}
    return {"status": "ok", "latencies": latencies}
