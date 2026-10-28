## Goal

Implement Phase 1 of [hackathon_spec.md](documents/hackathon_spec.md) (§6 step 1): the dependency-free biophysical foundation every later tier needs — continuous ODE state + suffix-only telemetry injection — plus the packaging and unit-test harness that proves it.

## Success Criteria

- `jamesian_layer.core` exposes `BiophysicalState`, RK4/Euler ODE solvers with τ-decay, the electro-thermal coil model, and a 10–50 Hz monotonic-clock daemon that runs without touching any LLM provider.
- `jamesian_layer.kv_cache` exposes a suffix-only formatter emitting the exact `<!-- SOMATIC_TELEMETRY: … -->` block from spec §5.2 and a prefix-invariance verifier.
- `pip install -e ".[dev]"` works on Python 3.10+ and `pytest tests/unit/ -v` passes the Phase 1 acceptance gates (§7.2): RK4 `O(dt⁴)` convergence, `V ∈ [-1, 1]`, coil steady-state error ≤ 0.5%, telemetry ≤ 45 tokens, prefix hash 100% match.
- No Phase 2+ scope leaks in: no comparator, breaker, loopline, middleware, audit, dashboard, or provider credentials.

## Approach

Greenfield build, bottom-up per spec §6: state dataclass first, then pure-function ODE solvers, then the daemon thread wrapping them, then the string-only suffix formatter. Keep Phase 1 fully offline and deterministic — no network, no tokenizer download, no Streamlit/FastAPI. Include `config.py` `Settings` in Phase 1 (threshold hierarchy, daemon frequencies, token budget per spec §8; provider keys default `None` and stay unused until Phase 3) so constants live in one place from the start. Reuse the exact dataclass fields, equations, constants, telemetry template, and regex from spec §4–§5 rather than inventing new shapes, so Phase 2 (comparator/breaker/habit) can consume `BiophysicalState` unchanged.

## Steps

1. **Packaging skeleton + config** — add `pyproject.toml` (PEP 621, `jamesian-layer`, `.[dev]` with `pytest`), `requirements.txt` (lower-bound pins per spec §12), `jamesian_layer/__init__.py` + `py.typed`, `tests/__init__.py`, `tests/unit/__init__.py`; add `config.py` `Settings` (thresholds, daemon defaults per spec §8; provider keys default `None`).
2. **`core/biophysical_state.py`** — `BiophysicalState` dataclass exactly per spec §5.1 (`sigma=0.20`, `valence=0.00`, `gamma=0.10`, `T_coil=25.0`, `current`, `rho_tau`, `mismatch_delta`, `timestamp_ns`) with `to_telemetry_dict()` rounding; clamp helpers for `sigma, gamma ∈ [0,1]`, `valence ∈ [-1,1]`.
3. **`core/ode_solvers.py`** — pure functions: RK4 stepper + Euler fallback, exponential τ-decay helper, `sigma/V/gamma` derivatives per spec §4.1 (σ₀=0.20/τ=45s, V τ=60s, γ₀=0.10/τ=30s, β_fail=1.50, α_vagal=0.80, κ_succ=0.40, κ_fail=0.60) and coil model per §4.2 (C_th=120 J/K, h=1.8 W/K, T_amb=25°C, R₀=0.32Ω, α_Cu=0.00393/K, warning 75°C, derate 85°C / recovery 72°C at 15% output clamp).
4. **`core/autonomic_daemon.py`** — background-thread/async daemon at configurable 10–50 Hz (default 20 Hz per spec §8) using `time.monotonic_ns`, `dt` clamp, start/stop/idempotent lifecycle, thread-safe latest-state snapshot + optional ring history; failure/success event hooks (`u_recovery`, `u_brace`, success/fail flags) wired to solver inputs, no provider imports.
5. **`kv_cache/suffix_formatter.py` + `prefix_verifier.py`** — `format_suffix(state)` appending the §5.2 tail block only (never touching the prefix), `TELEMETRY_PATTERN` regex extraction, token-budget check (target ≤ 40, hard cap ≤ 45; offline word/char estimator with a documented swap-in point for the Llama 3 tokenizer); verifier hashes turns `0..T-1` before/after to prove bit-level invariance.
6. **Unit tests + runbook** — `tests/unit/test_ode_solvers.py` (RK4 convergence vs. analytic decay, valence clamp, coil steady-state ≤ 0.5%, NaN-free long run) and `tests/unit/test_suffix_formatter.py` (suffix position, regex round-trip, token cap, prefix-hash invariance); minimal `conftest.py`; document `pip install -e ".[dev]"` and `pytest tests/unit/ -v` per spec §12.

## Validation Plan

- `pip install -e ".[dev]"` — expected: clean install, `import jamesian_layer` resolves.
- `pytest tests/unit/ -v` — expected: all Phase 1 tests pass (this is the §7.2 gate for `test_ode_solvers.py` / `test_suffix_formatter.py`).
- `pytest tests/unit/test_ode_solvers.py -v -k "convergence or clamp or steady_state"` — expected: RK4 error shrinks ~16× on halved `dt`, valence stays in bounds, coil steady-state error ≤ 0.5%.
- Manual: format a tool result and diff prefix bytes before/after — expected: identical prefix, telemetry block only at tail, regex extracts all six fields.

Highest-risk validation: the ≤ 45-token budget claim without a vendored Llama 3 tokenizer — run the estimator plus a character-length assertion, and flag exact-tokenizer verification as the one deferred check.

## Risks / Open Questions

- **Tokenizer source of truth:** spec §5.2 requires Llama 3 tokenizer counting; no tokenizer dep exists yet and downloads may be unavailable offline. Plan assumes an offline estimator + length cap for Phase 1, exact tokenizer check deferred to Phase 3 integration.

Open questions: None — all Phase 1 facts resolve to the spec and the empty repo tree.
