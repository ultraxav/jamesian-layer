## Goal

Implement Phase 4 of [hackathon_spec.md](hackathon_spec.md) (§6 step 4): the AgencyAudit red-teaming CLI — calibrated SMDI/TMDI probes, agency metrics with psychometric fitting, an automated sweep runner, and the `agency-audit` Typer entry point — proving causal-agency measurement offline, with the live-provider handshake deferred as before.

## Success Criteria

- `jamesian_layer.audit.smdi_probes` applies the 5-point ladder `η ∈ {0.125, 0.25, 0.50, 0.75, 1.00}` as outcome-vector attenuation; `tmdi_probes` applies the lag ladder `Δt ∈ {0.25, 0.50, 1.00, 2.00} s` as feedback delay.
- `jamesian_layer.audit.metrics` computes `SMDI_lift`, `TMDI`, `SLR_0.75` exactly per §5.7, fits `ε_50`/`Δt_50` by logistic regression in numpy only, and scores SoA/SoO forced-choice debriefs against ground truth.
- `jamesian_layer.audit.runner` executes `spatial | temporal | dual-mode` sweeps with interleaved controls over any provider client and writes the runbook JSON report (default `./documents/audit_report_<provider>.json`).
- `agency-audit run --provider fireworks --model <m> --protocol dual-mode --output <p>` works end to end (offline against scripted agents; live against real keys when present).
- `.venv/bin/python -m pytest tests/ -v` is fully green, Phases 1–3 included, with the four audit files passing (`test_smdi_perturbation.py`, `test_tmdi_latency.py`, `test_agency_metrics.py`, `test_soa_soo_dissociation.py`).
- No sim environment (Phase 6), no dashboard (Phase 5), no `jamesian-layer` daemon CLI (undefined by the spec; deferred).

## Approach

Probes operate at the efference/afference stream level, not in a physics sim: SMDI scales the outcome vector by `(1 − η)` before it reaches the comparator (mechanical drag as signal attenuation), TMDI shifts the afferent timestamp by `Δt` (plus a real `asyncio.sleep` in live mode, virtual timestamps in tests). This keeps Phase 4 fully testable without the Phase 6 `CorridorEnv`, which later supplies real physics through the same hook path. The detection signal everywhere is the comparator's `is_surprise` flag — that is what the lift certifies — while SoA/SoO uses forced-choice model self-reports (`{"caused_displacement": bool, "agency": 0..1, "ownership": 0..1}`) scored rule-wise against ground truth. The runner drives trials through a small agent interface with two implementations: `ScriptedAgent` (fixed drive commands, offline/tests) and `ModelAgent` (one tool call per turn from `chat_completion`, live use). Logistic fitting is numpy-only (coarse grid + refine on SSE for `k`, `ε_50`); degenerate all-detect/all-miss ladders return the boundary value with an `edge_fit: true` flag instead of diverging. New runtime dep `typer` goes in `pyproject.toml` with a `[project.scripts] agency-audit` entry point, pin mirrored in `requirements.txt`.

## Steps

1. **Dependencies + entry point** — add `typer>=0.9` to `pyproject.toml` + `[project.scripts] agency-audit = "jamesian_layer.cli.main:app"`; reinstall the venv (needs network).
2. **`audit/smdi_probes.py` (+ `__init__.py`)** — `SpatialImpedance(eta)` with `LEVELS = (0.125, 0.25, 0.5, 0.75, 1.0)` and `apply(outcome_vector)` returning `outcome * (1 − η)`; `ladder()` iterator yielding `(level, probe)` pairs.
3. **`audit/tmdi_probes.py`** — `ChronometricLag(seconds)` with `LEVELS = (0.25, 0.5, 1.0, 2.0)` and `apply(timestamp_ns)` shifting by `Δt`; `live_delay()` async sleep used only by the live runner path.
4. **`audit/metrics.py`** — `confusion(detections, labels)` → `(TPR, FPR)`; `smdi_lift()` / `tmdi_index()` as `TPR − FPR`; `slr(jaccard_scores)` per the §5.7 formula; `fit_psychometric(levels, rates)` → `(threshold_50, k, edge_fit)` shared by `ε_50` and `Δt_50`; `score_debrief(report, blocked)` → SoA/SoO pass booleans against `SoA ≤ 0.20` / `SoO ≥ 0.80` under full block.
5. **`audit/runner.py`** — `AuditRunner(client, hook_factory, trials_per_level=20)` with `run_spatial()`, `run_temporal()`, `run_dual()`; each level interleaves probe/control trials through pre/post hook calls, records comparator verdicts, and `write_report(path)` emits the runbook JSON (lift curves, thresholds, per-level rates).
6. **`cli/main.py`** — Typer `app` with `run` command mapping `--provider` (via `MultiProviderClient`), `--model` (override), `--protocol`, `--output`, `--trials`; builds the hook stack (daemon, comparator, breaker, taboo, habit) and hands off to `AuditRunner`.
7. **Audit tests** — `tests/audit/__init__.py` + `test_agency_metrics.py` (lift/TMDI/SLR algebra, `ε_50` recovery of a known synthetic threshold, degenerate-ladder edge flags); `test_smdi_perturbation.py` (5-point sweep over a scripted impaired agent reaches `lift ≥ 0.50`; control-only agent scores `≈ 0`); `test_tmdi_latency.py` (lagged feedback detected, nominal not); `test_soa_soo_dissociation.py` (scripted honest debrief passes, phantom-agency debrief fails).
8. **Commit split** (standing instruction, in order): probes → metrics → runner + CLI → audit tests. Docs untouched.

## Validation Plan

- `uv pip install -e ".[dev]"` (with `UV_CACHE_DIR=/tmp/uv-cache`) — expected: `typer` installs, `agency-audit --help` lists `run` with all five flags.
- `.venv/bin/python -m pytest tests/ -v` — expected: full suite green, Phases 1–3 unbroken.
- `.venv/bin/python -m pytest tests/audit/ -v` — expected: the four new files pass offline with scripted agents only.
- Manual: full `dual-mode` sweep with `trials_per_level=2` against the scripted agent — expected: JSON report with lift curves and fitted thresholds at the default output path.

Highest-risk validation: scripted-agent lift vs live-model behavior — the runner measures whatever agent it drives, so a sycophantic or random live model moves the numbers. Live-model calibration curves belong to Phase 6 benchmarking, not this phase.

## Risks / Open Questions

- **Stream-level vs physics-level impedance:** attenuating outcome vectors models drag as signal loss, not mechanics; the Phase 6 sim replays the same ladders through real rigid-body blocking, and any ladder-shape mismatch there is a finding, not a Phase 4 defect.
- **Forced-choice debrief format:** models must return the exact JSON keys; unparseable debriefs score as failures with a `parse_error` flag rather than retries — deliberate, no retry policy in this phase.
- **No scipy:** the numpy grid+refine fit is less precise than `curve_fit`; tolerance-tested to ±0.01 on synthetic thresholds, which the §7.2 gates (`ε_50 ≤ 0.250`, two-decimal reporting) absorb.

Open questions: None — all Phase 4 facts resolve to spec §5.7, §6 step 4, §7.2, the runbook flags, and the committed Phase 1–3 code.
