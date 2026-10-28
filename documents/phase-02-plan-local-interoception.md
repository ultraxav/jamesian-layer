## Goal

Implement Phase 2 of [hackathon_spec.md](hackathon_spec.md) (§6 step 2): the local interoception layer — efference-copy comparator, Jaccard taboo circuit-breaker, and subcortical habit/volition router — as pure, provider-free modules on top of the Phase 1 state, solvers, and `Settings`.

## Success Criteria

- `jamesian_layer.comparator` exposes `EfferenceCopy`, `AfferentFeedback`, and `EfferenceComparator.compare()` exactly per spec §5.3, with constructor defaults (0.25, 200.0 ms) mirroring `Settings.theta_surprise`; `lag_detector` tracks per-action dispatch latency.
- `jamesian_layer.breaker` trips at `J ≥ 0.70` over `k = 3` consecutive cycles, feeds a 10-cycle FIFO taboo buffer, and emits the §5.4 directive in the exact `[CIRCUIT_BREAKER_ACTIVE: TABOO_WORDS = [...]]` format.
- `jamesian_layer.loopline` cruises zero-token (`stride_forward`, `heartbeat_ping`, `idle_monitor`) while `mismatch < 0.15` and `σ < 0.60`, and escalates on surprise, high strain, or breaker trip.
- `.venv/bin/python -m pytest tests/unit/ -v` is fully green, Phase 1 tests included, with the three new test files passing the §7.2 gates.
- No provider imports, no daemon changes, no sim environment (Phase 6).

## Approach

Bottom-up, dependency-free: comparator first (pure linalg over caller-supplied vectors), then breaker (pure string-level, depends on nothing), then loopline (consumes `BiophysicalState` snapshots plus `Settings` thresholds, returns routine-or-escalate verdicts, never calls a provider). Constructor defaults repeat the spec literals so every module also works without a `Settings` instance. Decided with user: the comparator is dim-agnostic — vectors are caller-supplied odometry such as `[displacement, velocity]`; Phase 6's sim will supply them, no fixed dimension is enforced, and dim mismatch raises `ValueError`. Degenerate inputs clamp (negative lag to `0.0`, empty-union Jaccard to `0.0`); the stopword set is a frozen minimal built-in list. Split `loopline` per the tree: `habit_tracker` owns the CPG cruise state machine, `volition_gate` owns the escalate verdict.

## Steps

1. **`comparator/efference_comparator.py` (+ `__init__.py`)** — `EfferenceCopy`/`AfferentFeedback` dataclasses and `compare()` verbatim per §5.3 (`spatial_delta`, `chronometric_lag_ms`, `is_surprise`); dim-mismatched vectors raise `ValueError`; negative lag (synthetic clock skew) clamps to `0.0`.
2. **`comparator/lag_detector.py`** — `LagTracker` registry keyed by `action_id`: `note_efference()` / `note_afferent()` returning lag ms (`note_afferent` on an unknown id raises `KeyError`), `is_lagging()` against the 200 ms threshold, bounded size with oldest-entry eviction.
3. **`breaker/jaccard_detector.py`** — lowercase `[a-z0-9]+` tokenization with a small frozen built-in stopword set; `J_t` against the previous turn (`0.0` on empty union, so empty turns never trip); turn run-length counter (`run`) with `tripped` property and `reset()` — trips on the 3rd identical turn — thresholds defaulting to `theta_jaccard`/`jaccard_window_k`.
4. **`breaker/taboo_buffer.py`** — `deque(maxlen=10)` of per-turn token sets; `add_from_turn()` keeps the top-4 recurring non-stopwords, excluding pure digits with alphabetical tie-break for determinism; `directive()` renders the §5.4 string with sorted words for determinism; entries age out by maxlen (10-cycle decay).
5. **`loopline/habit_tracker.py` + `volition_gate.py` (+ `__init__.py`)** — `HabitTracker` with a routine registry mapping names to canned zero-token tool-call dicts; `step(state)` returns a routine name or escalation verdict with reason; `VolitionGate.escalate(mismatch, sigma, breaker_tripped)` centralizes the cruise condition. No threads here; 10 Hz pacing stays with the caller.
6. **Unit tests** — `test_efference_comparator.py` (nominal, spatial-only, lag-only, combined surprise, dim mismatch raises, negative lag clamps); `test_taboo_circuit_breaker.py` (trips exactly at k=3, silence below threshold, directive format, taboo decay after 10 cycles, stopwords never tabooed, empty turns never trip); `test_habit_tracker.py` (≥10 quiescent steps cruise without escalation, escalates on mismatch > 0.15, on σ ≥ 0.60, and on breaker trip; routine payloads contain no model calls).
7. **Commit split** (standing instruction, in order): comparator → breaker → loopline → tests. Docs untouched.

## Validation Plan

- `.venv/bin/python -m pytest tests/unit/ -v` — expected: all tests pass, Phase 1 included (no regressions).
- `.venv/bin/python -m pytest tests/unit/ -v -k "comparator or taboo or habit"` — expected: the 3 new files pass in isolation.
- Manual: feed the detector 3 identical tool-call strings — expected: trip with a 4-word directive; feed the tracker 10 quiescent states then `mismatch=0.5` — expected: cruise, then escalate with reason.

Highest-risk validation: Jaccard edge cases (empty turns, pure-boilerplate turns) — pinned by explicit tests asserting `J = 0.0` and no trip.

## Risks / Open Questions

- **Vector semantics:** decided dim-agnostic; if Phase 6 needs typed odometry fields, the dataclasses gain optional metadata without changing `compare()`.
- **Stopword list:** decided frozen minimal built-in, documented in-module; benchmark tuning may extend it later without changing the detector API.

Open questions: None — all Phase 2 facts resolve to spec §5.3–§5.5, §6 step 2, §7.2, and the committed Phase 1 code.
