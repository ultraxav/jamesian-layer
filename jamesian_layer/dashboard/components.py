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
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                title={"text": title, "font": {"size": 13}},
                number={"font": {"size": 24}},
                gauge=gauge,
            )
        )
        fig.update_layout(height=175, margin={"t": 36, "b": 10, "l": 18, "r": 18})
        figures.append(fig)
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


def corridor_2d_figure(
    frame: dict,
    trail: list[dict],
    arm: str = "jamesian",
    barrier_pos: float = 25.0,
) -> go.Figure:
    """2D top-down corridor map showing obstacle wall, bypass lane, path trail, and rover."""
    fig = go.Figure()

    # Outer corridor walls (x: 0..100m, y: -1.0..+1.0m)
    fig.add_shape(
        type="rect",
        x0=0.0,
        y0=-1.0,
        x1=100.0,
        y1=1.0,
        line={"color": "#64748b", "width": 2},
        fillcolor="rgba(15, 23, 42, 0.35)",
        layer="below",
    )

    # Center approach lane guide (y = 0.0) and upper bypass lane guide (y = +0.65)
    fig.add_shape(
        type="line",
        x0=0.0,
        y0=0.0,
        x1=barrier_pos,
        y1=0.0,
        line={"color": "rgba(148, 163, 184, 0.35)", "width": 1, "dash": "dot"},
        layer="below",
    )
    fig.add_shape(
        type="line",
        x0=barrier_pos,
        y0=0.65,
        x1=100.0,
        y1=0.65,
        line={"color": "rgba(16, 185, 129, 0.40)", "width": 1.5, "dash": "dash"},
        layer="below",
    )

    # Goal finish zone at x = 96..100m
    fig.add_shape(
        type="rect",
        x0=96.0,
        y0=-1.0,
        x1=100.0,
        y1=1.0,
        fillcolor="rgba(16, 185, 129, 0.18)",
        line={"color": "rgba(16, 185, 129, 0.5)", "width": 1},
        layer="below",
    )

    # Red obstacle barrier at x = 25.0m blocking the center lane (y: -0.98 to +0.35),
    # leaving the upper bypass channel (y: +0.35 to +0.98) open for steering.
    fig.add_shape(
        type="rect",
        x0=barrier_pos - 0.8,
        y0=-0.98,
        x1=barrier_pos + 0.8,
        y1=0.35,
        fillcolor="rgba(220, 38, 38, 0.85)",
        line={"color": "#ef4444", "width": 2},
    )

    # Labels for Barrier, Bypass Lane, and 100m Goal
    fig.add_annotation(
        x=barrier_pos,
        y=-0.78,
        text="🧱 WALL (25m)",
        showarrow=False,
        font={"size": 11, "color": "#fca5a5"},
    )
    fig.add_annotation(
        x=60.0,
        y=0.84,
        text="↗ CLEAR BYPASS LANE (y = +0.65m)",
        showarrow=False,
        font={"size": 10, "color": "#6ee7b7"},
    )
    fig.add_annotation(
        x=98.0,
        y=-0.78,
        text="🏁 100m",
        showarrow=False,
        font={"size": 10, "color": "#6ee7b7"},
    )

    # Historical path trail from Cycle 1 up to current cycle
    if trail:
        xs = [0.0] + [float(f.get("x", f.get("position", 0.0))) for f in trail]
        ys = [0.0] + [float(f.get("y", 0.0)) for f in trail]
        trail_color = "#38bdf8" if arm == "jamesian" else "#f87171"
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines+markers",
                line={"color": trail_color, "width": 3, "dash": "solid"},
                marker={"size": 6, "color": trail_color},
                name="path",
                hoverinfo="skip",
            )
        )

    # Current rover coordinates & visual state
    x_now = float(frame.get("x", frame.get("position", 0.0)))
    y_now = float(frame.get("y", 0.0))
    blocked = bool(frame.get("blocked", False))
    derated = bool(frame.get("derated", False))
    phase = str(frame.get("phase", ""))
    source = str(frame.get("source", "LLM_CORTICAL"))
    t_coil = float(frame.get("T_coil", 25.0))

    if derated:
        rover_color = "#dc2626"
        halo_color = "rgba(220, 38, 38, 0.35)"
        badge = f"🔥 DERATED ({t_coil:.1f}°C)"
    elif blocked:
        rover_color = "#f59e0b" if arm == "jamesian" else "#ef4444"
        halo_color = "rgba(245, 158, 11, 0.30)" if arm == "jamesian" else "rgba(239, 68, 68, 0.30)"
        badge = f"⚡ STALL 20A ({t_coil:.1f}°C)" if arm == "jamesian" else f"💥 STUCK AT WALL ({t_coil:.1f}°C)"
    elif phase == "escape_maneuver":
        rover_color = "#06b6d4"
        halo_color = "rgba(6, 182, 212, 0.28)"
        badge = f"🔄 STEERING ({frame.get('tool', 'turn_bearing')})"
    elif source == "HABIT_ROUTER":
        rover_color = "#10b981"
        halo_color = "rgba(16, 185, 129, 0.25)"
        badge = f"⚡ 0-TOKEN HABIT ({x_now:.0f}m)"
    else:
        rover_color = "#3b82f6" if arm == "jamesian" else "#60a5fa"
        halo_color = "rgba(59, 130, 246, 0.22)"
        badge = f"🚗 DRIVE ({x_now:.1f}m)"

    # Outer halo ring around the rover
    fig.add_trace(
        go.Scatter(
            x=[x_now],
            y=[y_now],
            mode="markers",
            marker={"size": 30 if (blocked or derated) else 24, "color": halo_color},
            hoverinfo="skip",
        )
    )
    # Main rover marker + status label
    fig.add_trace(
        go.Scatter(
            x=[x_now],
            y=[y_now],
            mode="markers+text",
            marker={
                "size": 16,
                "color": rover_color,
                "line": {"color": "#ffffff", "width": 2},
                "symbol": "triangle-up" if phase == "escape_maneuver" else "circle",
            },
            text=[badge],
            textposition="top center" if y_now <= 0.2 else "bottom center",
            textfont={"size": 11, "color": "#f8fafc"},
            name="rover",
        )
    )

    fig.update_layout(
        height=230,
        showlegend=False,
        margin={"t": 12, "b": 32, "l": 12, "r": 12},
        xaxis={
            "range": [-3, 104],
            "title": "Corridor Position (m)",
            "gridcolor": "rgba(148, 163, 184, 0.15)",
            "zeroline": False,
        },
        yaxis={
            "range": [-1.15, 1.15],
            "visible": False,
        },
    )
    return fig

