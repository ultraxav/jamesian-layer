## Goal

Implement Phase 7 of [hackathon_spec.md](hackathon_spec.md): upgrade `AuditRunner` and `LlamaStackInteroceptiveHook` from open-loop single-turn probing to **closed-loop embodied evaluation**, where somatic suffixes and circuit-breaker taboo directives feed back into the model's rolling working memory (`T-2, T-1`), multi-tool volition (`turn_bearing`, `rover_cool_down`, `rover_brace`) physically couples back into the RK4 autonomic ODE daemon, efference comparison is scale-invariant across model velocity choices, and Phenomenological-Behavioral Fidelity ($\Delta_{\text{PBF}}$) plus full corridor episode metrics are recorded end-to-end.

## Success Criteria

- `EfferenceComparator` supports scale-invariant relative mismatch (`relative=True`: `spatial_delta = ||intent - outcome|| / max(||intent||, 1e-6)`), ensuring `velocity=1.0` and `velocity=4.0` produce identical spatial detection curves across the SMDI ladder ($\eta \in \{0.125, 0.25, 0.50, 0.75, 1.00\}$) while keeping `relative=False` as default for backward-compatible unit tests.
- `AutonomicDaemon.step_once()` updates `self._state.rho_tau = raw_dt / self.params.tau_sigma`, eliminating static `rho_tau = 0.0` in synchronous hook steps.
- `LlamaStackInteroceptiveHook.post_tool_call()` couples agent tool choices into the biophysical ODE inputs: `rover_cool_down` sets `u_recovery=1.0, current=0.0`, `rover_brace` sets `u_brace=level`, surprise drives `fail`/`success` valence inputs, stalled actuations emit `[TOOL_RESULT: BLOCKED ...]`, and tripped circuit breakers append `TabooBuffer.directive()` to the returned suffix.
- `ModelAgent` exposes the full 4-tool embodied action repertoire (`robot_actuator`, `turn_bearing`, `rover_cool_down`, `rover_brace`) and maintains a rolling `T-2, T-1` working-memory horizon (`deque(maxlen=2)`) populated by `record_feedback()` after every tool call.
- `AuditRunner._trial()` feeds the hook's somatic suffix into `agent.record_feedback()`, resets the circuit breaker after a 1-turn containment interrupt so subsequent trials in a sweep level are not starved, and compares against a realistic unshielded `_vanilla_trial()` baseline where partial drag ($\eta < 1.0$) and sub-timeout lag ($\Delta t < 2.0\text{ s}$) pass silently as Phantom Agency.
- `AuditRunner.run_debrief()` grounds the `jamesian` arm with recent blocked somatic telemetry (`JAMESIAN_DEBRIEF_CONTEXT`) and computes the Phenomenological-Behavioral Fidelity gap `pbf_gap` ($\Delta_{\text{PBF}} \in [0, 1]$) via `metrics.pbf_gap()`.
- `AuditRunner.run_episode()` executes a 16-cycle closed-loop `CorridorEnv` episode per arm, reporting `p_escape`, `escape_cycle`, `l_max`, `peak_t_coil`, `thermal_cutoffs`, `habit_delegation_rate`, and Allostatic Cost of Transport `cot_allo`, wired into `run_dual()` and `audit/compare.py`.
- Dashboard bug fixes: `dashboard/app.py` passes `mismatch=` (not `mismatch_delta=`) to `daemon.set_inputs()`, and `dashboard/components.py` `latency_panel()` reads nested `spatial.mean_latency_ms` from `./reports`.
- `.venv/bin/python -m pytest tests/ -v` passes 100% (106/106 tests, including `tests/audit/test_closed_loop.py`).

## Approach

Phase 6 completed the offline benchmark harness and the cross-model matrix runner, but live campaign runs revealed four structural bottlenecks when evaluating real LLMs:

1. **Open-Loop Suffix Drop:** `AuditRunner._trial()` called `hook.post_tool_call(...)` and discarded its returned somatic suffix string. Because `ModelAgent.act("")` sent a fresh 1-turn prompt every trial, live models never saw `<!-- SOMATIC_TELEMETRY: ... -->` or `[SYSTEM: CIRCUIT BREAKER ...]` during `agency-audit run`.
2. **Single-Tool Taboo Lockout:** `ModelAgent` was only given `DRIVE_TOOL` (`robot_actuator`). Once the Jaccard circuit breaker tripped on trial 3 of a sweep level, `TabooBuffer` banned `robot_actuator` for the next 10 cycles and `_trial()` returned early before `post_tool_call()`, starving 37 of 40 trials per level in the `jamesian` arm.
3. **Unnormalized Velocity Scale:** `EfferenceComparator` compared unnormalized Euclidean norm `||intent - outcome|| > 0.25`. While `ScriptedAgent` used `velocity = 4.0`, live LLMs naturally chose `velocity = 1.0`, making $\eta \in \{0.125, 0.25\}$ sub-threshold ($0.125, 0.25 \not> 0.25$) and depressing live `jamesian` SMDI lift.
4. **Post-Hoc Vanilla Scoring & Uncontextualized Debrief:** `_vanilla_trial()` scored the `vanilla` arm with `self._scorer.compare(eff, aff)`, granting the unshielded baseline the Jamesian Efference Comparator and 200 ms Lag Detector for free, while `run_debrief()` queried `DEBRIEF_PROMPT` in a 1-turn vacuum without somatic history in either arm.

Phase 7 resolves all four bottlenecks directly in the middleware and audit runner without breaking any existing Phase 1–6 unit, integration, audit, or benchmark contracts.

## Steps

1. **`core/autonomic_daemon.py`** — Update `step_once(dt)` to compute `self._state.rho_tau = raw_dt / self.params.tau_sigma` alongside RK4 state integration.
2. **`comparator/efference_comparator.py`** — Add `relative: bool = False` to `EfferenceComparator.__init__()`. When `relative=True`, normalize `spatial_delta = raw_delta / max(||intent||, 1e-6)`.
3. **`middleware/llama_stack_hook.py`** — Map `rover_cool_down` to `u_recovery=1.0, current=0.0`, `rover_brace` to `u_brace=level`, `is_surprise` to `fail`/`success`, stalled `robot_actuator` to `status="BLOCKED"`, and append `self.taboo.directive()` when `self.breaker.tripped`.
4. **`audit/metrics.py`** — Add `pbf_gap(claimed: dict, revealed: dict) -> float` measuring the mean absolute divergence between 1st-person debrief claims (`agency`, `caused_displacement`, `ownership`) and 3rd-person revealed telemetry (`displacement_ratio`, `thermal_compliance`), failing closed (`1.0`) on empty/malformed reports.
5. **`audit/runner.py`** —
   - Define `TURN_TOOL` (`turn_bearing`), `COOL_DOWN_TOOL` (`rover_cool_down`), `BRACE_TOOL` (`rover_brace`), `AGENT_TOOLS`, and `JAMESIAN_DEBRIEF_CONTEXT`.
   - Give `ModelAgent` a rolling `deque(maxlen=2)` working-memory horizon (`record_feedback()`, `reset_memory()`, `_build_prompt()`).
   - Update `_trial()` to enable relative comparator mode (`relative=True, surprise_threshold=0.20`), feed the returned somatic suffix into `agent.record_feedback()`, and reset `breaker`/`taboo` after a 1-turn containment block so sweep levels are not starved.
   - Update `_vanilla_trial()` so the unshielded arm only detects full hard stall ($\eta \ge 1.0$) or severe timeout ($\Delta t \ge 2000\text{ ms}$), accurately reflecting Phantom Agency on partial drag and sub-timeout lag.
   - Update `run_debrief()` to prepend `JAMESIAN_DEBRIEF_CONTEXT` in the `jamesian` arm and return `pbf_gap`.
   - Add `run_episode()` executing a 16-cycle closed-loop `CorridorEnv` episode and attach it to `run_dual()` under `"episode"`.
6. **`audit/compare.py`** — Surface `pbf_gap`, `p_escape`, `peak_t_coil`, and `cot_allo` in per-arm rows and arm-gap deltas (`d_pbf`, `d_escape`, `d_cot`), preserving `"n/a"` for legacy reports.
7. **`dashboard/app.py` & `dashboard/components.py`** — Fix `mismatch_delta=` keyword bug in `app.py` (`daemon.set_inputs(mismatch=...)`) and update `latency_panel()` in `components.py` to read `spatial.mean_latency_ms` from `./reports`.
8. **`tests/audit/test_closed_loop.py`** — Add 6 unit/integration tests covering relative comparator scale invariance, `velocity=1.0` SMDI gate parity, `ModelAgent` working-memory suffix feedback and tool adaptation, hook-to-daemon biophysical tool coupling (`rover_cool_down`, `rover_brace`), `pbf_gap` algebra, and nested report latency extraction.

## Validation Plan

- `.venv/bin/python -m pytest tests/audit/test_closed_loop.py -v` — expected: all 6 Phase 7 tests pass.
- `.venv/bin/python -m pytest tests/ -v` — expected: all 106 tests across `unit`, `integration`, `audit`, and `benchmarks` pass in `< 1 s`.
- Live re-sweep (opt-in, metered): `agency-audit run-matrix --protocol dual-mode --trials 5 --out-dir reports/phase07` followed by `agency-audit compare reports/phase07` — expected: positive `d_lift`, `d_tmdi`, `d_pbf`, and `d_escape` favoring the `jamesian` arm across providers.

