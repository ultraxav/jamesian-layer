## Goal

Implement Phase 5 of [hackathon_spec.md](hackathon_spec.md) (§6 step 5): a 100% pure-Python Streamlit + Plotly dashboard that renders the running daemon's biophysical state, Jaccard repetition index, and manual disruption controls at 10 Hz — with no JavaScript, no provider credentials, and no sim environment required.

## Success Criteria

- `jamesian_layer.dashboard.buffer` exposes a thread-safe bounded ring buffer (`collections.deque(maxlen=300)`) fed by the daemon.
- `jamesian_layer.dashboard.components` builds Plotly gauge indicators (σ, V, γ, T_coil), electro-thermal strip charts, and a multi-provider latency panel — all from plain data, with no Streamlit imports.
- `jamesian_layer.dashboard.app` is pure-Python Streamlit using `@st.fragment(run_every="100ms")`, a `st.cache_resource` daemon + buffer singleton, and sidebar disruption buttons that drive daemon inputs.
- `streamlit run jamesian_layer/dashboard/app.py` streams smoothly at 10 Hz with no blocking, no JavaScript, and no network calls.
- `.venv/bin/python -m pytest tests/ -v` is fully green, Phases 1–4 included, plus the new dashboard unit tests.
- No sim (Phase 6), no audit CLI changes, no new provider code.

## Approach

The daemon already runs on a background thread and exposes snapshots via `get_state()`; the dashboard only reads. A `st.cache_resource` singleton owns one daemon plus one buffer so Streamlit reruns never duplicate threads, and a `@st.fragment(run_every="100ms")` renderer polls the buffer without blocking the page. Figure builders take plain snapshot lists and return Plotly figures, keeping all Streamlit calls in `app.py` — that split makes the builders unit-testable without a server. Manual disruption buttons write synthetic scenarios straight into daemon inputs (`current=20.0` for stall heating, `mismatch` spikes for surprise, `u_brace`/`u_recovery` toggles); they are explicitly scenario drivers until the Phase 6 sim supplies real physics. The multi-provider latency panel reads the JSON reports in `./documents/` when present and shows an explicit "no runs yet" state otherwise — never fabricated data. New runtime deps (`streamlit>=1.37`, `plotly>=5.0`, already pinned in `requirements.txt`) go in `pyproject.toml` dependencies; reinstall needs network.

## Steps

1. **Dependencies** — add `streamlit>=1.37`, `plotly>=5.0` to `pyproject.toml`; reinstall the venv (`uv pip install -e ".[dev]"`, needs network).
2. **`dashboard/buffer.py` (+ `__init__.py`)** — `TelemetryBuffer` wrapping `deque(maxlen=300)` with a lock; `append(state: BiophysicalState)`, `snapshot(n)` returning the newest-n telemetry dicts oldest-first, `clear()`; drops oldest silently when full (documented, never blocks the daemon thread).
3. **`dashboard/components.py`** — pure builders: `gauges(latest)` (four Plotly indicators with spec ranges and the 75/85 °C thermal bands on the coil gauge), `strip_charts(history)` (σ/V/γ/T_coil time series), `jaccard_panel(score, tripped)` (repetition index + breaker state), `latency_panel(reports_dir)` (per-provider `mean_latency_ms` from `./documents/audit_report_*.json`, explicit empty state otherwise; runner reports gained that field in this phase to feed it).
4. **`dashboard/app.py`** — `st.set_page_config`, `st.cache_resource` singleton (`daemon.start()` once, `TelemetryBuffer`, shared `JaccardDetector` fed each tick), `@st.fragment(run_every="100ms")` renderer appending `daemon.get_state()` per tick, sidebar buttons: stall (current 20 A), surprise burst, brace/recover toggles, reset; Jaccard text input box observed into the detector each tick so repetition is visible without a sim.
5. **Unit tests** — `tests/unit/test_dashboard_buffer.py` (bounded eviction order, snapshot slicing, clear; gauge/strip builders return figures with expected traces from synthetic history). Addition beyond the spec tree, which names no dashboard test file; covers the only new logic that can run headless.
6. **Commit split** (standing instruction, in order): deps → buffer + components → app → dashboard tests. Docs untouched.

## Validation Plan

- `uv pip install -e ".[dev]"` (with `UV_CACHE_DIR=/tmp/uv-cache`) — expected: `streamlit`, `plotly` install cleanly.
- `.venv/bin/python -m pytest tests/ -v` — expected: full suite green, Phases 1–4 unbroken, new buffer/figure tests pass.
- `.venv/bin/python -c "import jamesian_layer.dashboard.app"` — expected: imports without starting a server or threads.
- Manual: `streamlit run jamesian_layer/dashboard/app.py`, press stall — expected: coil gauge climbs toward the 75 °C band, Jaccard panel trips on repeated input, no page reloads, no browser-console JavaScript of ours.

Highest-risk validation: Streamlit's fragment rerun interacting with the background daemon thread (duplicated threads, stale locks) — mitigated by the `cache_resource` singleton plus the headless import check, but the only real proof is the live manual run above.

## Risks / Open Questions

- **`@st.fragment(run_every="100ms")` API drift:** the plan follows the spec's pinned call; if the installed Streamlit version changed the signature, adapt `app.py` to the real API and note the delta — figure builders and buffer are unaffected.
- **Synthetic disruption controls:** buttons fake stall/surprise through daemon inputs rather than real physics; clearly labeled in the UI as scenario drivers until Phase 6 replaces them with `CorridorEnv` truth.
- **Latency panel without live runs:** shows "no runs yet" until audit reports exist; the panel never invents numbers.

Open questions: None — all Phase 5 facts resolve to spec §5.8, §6 step 5, §12, and the committed Phase 1–4 code.

---

## Addendum: Client-Side Embedded Architecture Evolution & High-DPI Polish

### 1. Motivation
The original Phase 5 implementation utilized server-driven Streamlit fragments (`@st.fragment(run_every="100ms")`) to pull data from a Python ring buffer and update Plotly charts over a WebSocket connection. During live stress testing, two critical friction points emerged:
1. **WebSocket Lag & DOM Destruction**: Polling at 10 Hz over Streamlit's WebSocket caused perceptible stutter, DOM rebuild churn, and browser micro-freezes.
2. **High-DPI / Aspect-Ratio Distortion**: Static canvas dimensions (600×140) scaled with CSS `width: 100%` distorted circles into horizontal ellipses and produced pixelation/blurriness on high-DPI (Retina / 1.5× / 2.0× scaling) screens.

### 2. Architectural Solution
Both dashboards were refactored into high-performance, client-side embedded architectures hosted via `st.iframe`:
* **Live Telemetry & Biophysical Oscilloscope (`app.py` & `live_monitor.html`)**:
  - Embedded client-side Runge-Kutta 4th Order (RK4) ODE solver executing continuous physical integration.
  - Zero-latency HTML5 canvas biophysical oscilloscope rolling traces ($\sigma, V, \gamma, T_{\text{coil}}$).
  - Dynamic Device Pixel Ratio (DPR) resolution scaling: auto-adjusts `canvas.width = rect.width * dpr` with `ctx.scale(dpr, dpr)` for razor-sharp rendering at all monitor DPIs.
  - Interactive live perturbation injections (`Stall Actuator 20 A`, `Surprise Burst η=0.9`, `Toggle Brace`, `Active Cool Down`, `Reset to Cruise`).
  - Interactive 3-strike Jaccard anti-recidivism breaker and Taboo buffer test arena.
  - Cached multi-provider latency analytics (`@st.cache_data`) aggregating real campaign runtimes across Meta, Baseten, and LM Studio.
* **Synchronized 2D Corridor Replay (`demo_app.py` & `viewer.html`)**:
  - Synchronized head-to-head replay of pre-recorded Table 4.2 *ceteris paribus* traces across Meta and open-weight models (`muse-spark-open-1026` Rank #1 on Baseten, `muse-spark-1.3` on Meta API, followed by Gemma models).
  - Dynamic DPR-scaled 2D corridor canvas with 1:1 true-circle rover rendering, crisp vector labels, interactive scrub bar, milestone jumps, and side-by-side metric scorecards.
