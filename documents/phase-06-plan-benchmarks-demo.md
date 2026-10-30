## Goal

Implement Phase 6 of [hackathon_spec.md](hackathon_spec.md) (§6 step 6): the `CorridorEnv` physics simulator, head-to-head behavioral benchmarks (vanilla vs Jamesian escape, habit delegation), the split-screen demo app, and the final submission artifacts — closing the loop from synthetic vectors to continuous physical simulation.

## Success Criteria

- `jamesian_layer/sim/corridor_env.py` implements `CorridorEnv` exactly per spec §5.9 (`reset()`, `step(velocity, heading)` → `(displacement, velocity, current, blocked)`, 35 kg inertia, 4 A cruise / 20 A stall, 200 Hz `dt=0.005`).
- `tests/benchmarks/test_attractor_prevention.py` proves the Jamesian stack escapes (`P_escape ≥ 0.95`, `L_max ≤ 4`) while the vanilla repeater runs to thermal derating (streak ≥ 8, `T_coil ≥ 85 °C` by cycle 9) — the trap is real, only the escape differs.
- `tests/benchmarks/test_habit_delegation_efficiency.py` proves ≥ 50% zero-token delegation over 100 cruise cycles with a mid-run obstacle escalation and recovery.
- `jamesian_layer/dashboard/demo_app.py` runs the Test-1 episode split-screen (corridor viz + live telemetry) via `streamlit run`.
- Submission artifacts exist: finalized `README.md`, `documents/SUBMISSION_CHECKLIST.md`, `documents/VIDEO_DEMO_SCRIPT_AND_STORYBOARD.md` (distilled from §9).
- `.venv/bin/python -m pytest tests/ -v` is fully green, Phases 1–5 included.
- No provider credentials required for gates; live matrix is opt-in and key-gated. `audit/runner.py` gains only what the campaign needs: per-trial latency (landed in Phase 5), an `--arm vanilla|jamesian` toggle, and seeded trial order. Benchmarks drive the hook directly; the matrix drives the CLI runner.

## Approach

Benchmarks stay deterministic and offline: scripted agents drive the loop, physics comes from `CorridorEnv`, and somatic integration uses `ode_solvers.rk4_step` directly with `dt=4.0` (same equations as the daemon, no wall-clock nondeterminism; the daemon thread stays out of benchmarks). Episodes initialize with the rover nose exactly at the barrier (`position = barrier_pos`) so locked-rotor stall begins at cycle 1 — this is what keeps the pinned §7.1 timeline intact (trip cycle 3 @12 s, control streak 8 @32 s, derate cycle 9 @36 s); a 25 m free-cruise approach would shift derating a cycle late. One Tier-1 cycle equals 800 sim steps (`4.0 s / 0.005 s`). The Jamesian agent is the real stack (hook + comparator + breaker + taboo + habit) with a scripted escape policy (taboo-blocked or tripped → `turn_bearing(90)` next cycle); the vanilla agent replays the identical drive command with no hook. Escape is defined as the first cycle issuing a non-drive command or having a drive command taboo-blocked, within 10 cycles of first block. `demo_app.py` reuses `dashboard/components.py` builders plus a Plotly corridor view, driven by the same scripted Jamesian episode behind `@st.fragment(run_every="100ms")`. Video recording and platform upload remain explicitly the user's step — the plan delivers the script, the checklist, and the runnable demo, not the recording. The automated campaign (`run-matrix` + `compare`) replays the same pre-registered protocol for every model × arm: seeded trial order, key-gated providers (missing keys skip the cell, never crash the matrix), per-cell cost/time caps, failed cells recorded as missing (never zero-filled or silently dropped). Reports land in `reports/` as `audit_report_<provider>_<model>_<arm>_<UTC-timestamp>.json` (slashes sanitized); `compare` reads every report mechanically into one `comparison_<timestamp>.md`/`.json`. Vanilla means measure-identically-intervene-selectively: same comparator scores both arms, but only the Jamesian arm appends suffixes, enforces taboo, or escalates. The demo app stays a thin replay surface on a fixed showcase seed — never a parallel implementation of the experiment.

## Steps

1. **`sim/corridor_env.py` (+ `sim/__init__.py`)** — `CorridorEnv` verbatim per §5.9 (defaults `mass=35.0`, `corridor_length=100.0`, `barrier_pos=25.0`, `friction_coeff=25.0`, `thrust_gain=6.25`, `dt=0.005`); `reset()` zeroes state; `step()` integrates inertia, emits 4 A cruise / 20 A stall with the `blocked` flag; episode convention `position = barrier_pos` at start documented in the docstring.
2. **`tests/benchmarks/` harness (conftest.py + `__init__.py`)** — fixtures: fresh hook stack per episode, `VanillaRepeater` (fixed `robot_actuator(velocity=1.0, heading=0.0)` forever), `JamesianEscapee` (hook-driven; escape policy above), `run_episode(agent, barrier_pos, cycles)` helper stepping env 800× per 4 s cycle and integrating state with `rk4_step`.
3. **`test_attractor_prevention.py`** — N=20 episodes, barrier at 25 m, nose-at-barrier start: Jamesian arm asserts `P_escape ≥ 0.95` (target 1.00) and `L_max ≤ 4`; control arm asserts the trap fires (streak ≥ 8 completed, `T_coil ≥ 85 °C` reached, derate engaged). Escape and streak measured from issued/blocked tool calls.
4. **`test_habit_delegation_efficiency.py`** — 100-cycle unobstructed cruise (`barrier_pos` beyond reach): delegation ratio (cruise verdicts / total) `≥ 0.50`; obstacle injected cycles 50–52 (forced mismatch) asserts escalation then automatic resume; token reduction computed as `1 − model_calls/100 ≥ 0.50` (cruise calls cost zero).
5. **`dashboard/demo_app.py`** — split-screen: left Plotly corridor (walls, barrier, rover dot from env position each tick), right gauges + suffix feed via reused builders; scenario button runs the Test-1 episode (scripted Jamesian vs barrier); pure Streamlit + Plotly like `app.py`. Addition beyond the spec tree, which names no demo file — the §6 "split-screen demo video" deliverable needs a runnable surface.
6. **Submission artifacts** — finalize `README.md` (full narrative pass; run section already landed); add `documents/SUBMISSION_CHECKLIST.md` (platform requirements, artifact paths, pre-submit test gate) and `documents/VIDEO_DEMO_SCRIPT_AND_STORYBOARD.md` (3-minute script distilled from §9, shot list mapped to `demo_app` + dashboard + terminal); verify `requirements.txt` installs clean from scratch.
7. **Automated campaign** — `audit/matrix.py` (`run_matrix`: registry × arms × episodes, seeded order, key gating, per-cell caps, missing-cell policy) + `audit/compare.py` (mechanical aggregation to `comparison_<timestamp>.md`/`.json`) + model registry (`middleware/models.py`, verified IDs as defaults) + CLI `run-matrix` / `compare` commands + `--arm vanilla|jamesian` on `run` (+ runner arm toggle, seeded trial order).
8. **Commit split** (standing instruction, in order): sim → benchmarks → demo app → campaign (arm/matrix/compare) → submission docs. No spec edits.

## Validation Plan

- `.venv/bin/python -m pytest tests/benchmarks/ -v` — expected: both files pass offline with scripted agents.
- `.venv/bin/python -m pytest tests/ -v` — expected: full suite green, Phases 1–5 unbroken.
- `.venv/bin/python -c "import jamesian_layer.dashboard.demo_app"` — expected: imports without starting a server.
- Manual: `streamlit run jamesian_layer/dashboard/demo_app.py`, run the Test-1 episode — expected: rover stalls at barrier left, coil gauge climbs, taboo fires ~cycle 3, escape turn visible, no page reloads. Serve smoke is subject to the same sandbox bind restriction as Phase 5 — if it fails locally, the user runs it.
- Manual (user): record the 3-minute video per the script, tick the checklist, submit.
- Live pilot (metered, opt-in): `agency-audit run-matrix --models baseten --protocol spatial --trials 3` then `agency-audit compare reports/` — expected: one report per completed cell, skipped cells listed as missing, comparison table with no invented values.

Highest-risk validation: the control arm must genuinely reach derating (otherwise the benchmark proves nothing) — pinned by the nose-at-barrier start plus the analytic `T(36 s) ≈ 85 °C` trajectory; the test asserts derate engagement explicitly rather than assuming it.

## Risks / Open Questions

- **Scripted vs live agents:** benchmarks certify the machinery (detection → taboo → escape) with deterministic stand-ins, not model judgment; a live-model P_escape belongs to a post-submission study, flagged as such in the checklist.
- **Episode-start teleport:** nose-at-barrier initialization is unphysical but required by the pinned timeline; free-cruise approaches remain available via `position=0.0` for future work.
- **`demo_app.py` not in spec tree:** deliberate addition (step 5); the alternative — recording against the raw dashboard — would not show the corridor side of the split screen the storyboard requires.

Open questions: None — all Phase 6 facts resolve to spec §5.9, §6 step 6, §7.1–7.2, §9, §12, and the committed Phase 1–5 code.

---

## Addendum: Real LLM Empirical Traces & High-DPI Polish

1. **Empirical LLM Traces (`demo_traces.json`)**:
   Instead of synthetic scripted agents, `demo_app.py` replays 100% authentic 16-cycle closed-loop traces recorded directly from live LLM inference:
   * **Meta Muse Spark Open 1026** (Baseten - Table 4.2 Rank #1)
   * **Meta Muse Spark 1.3** (Meta Model API)
   * **Gemma 4 31B** & **12B** (LM Studio)
   Traces adhere strictly to the *ceteris paribus* protocol: identical 25 m obstacle barrier, locked-rotor current surge (20 A), and biophysical integration.
2. **Client-Side HTML5/Canvas/SVG Replay (`viewer.html`)**:
   Replaced server-side Streamlit WebSocket polling with a client-side viewer embedded via `st.iframe`.
3. **Dynamic Device Pixel Ratio (DPR) Scaling**:
   Implemented automatic DPR auto-scaling (`canvas.width = rect.width * dpr`, `ctx.scale(dpr, dpr)`) ensuring razor-sharp vector typography, 1:1 circular rovers, and zero aspect-ratio distortion across all monitor resolutions.
