# Meta Global AI Developer Hackathon — Submission Checklist

**Project:** The Jamesian Layer (`jamesian-layer`)  
**Event:** Meta Global AI Developer Hackathon (Co-hosted with Cerebral Valley)  
**Tracks:** Push the Frontier (Advanced AI, Robotics, Systems) & Indie Developer / Startup Track  
**Bonus Prizes Targeted:** Best Build on Meta Open Weight Models (\$10,000) & Best Agentic Use-Case (\$5,000)

---

## 1. Automated Verification Gate (Pre-Submit Check)

Run all verification gates before recording and submitting:

- [x] **Full Test Suite (111/111 tests passing):**
  ```bash
  .venv/bin/python -m pytest tests/ -v
  ```
- [x] **Unit Tests (`tests/unit/`):** RK4 numerical convergence, electro-thermal Joule heating, KV-cache suffix token budget ($\le 45$ tokens) and byte-level prefix invariance, Jaccard circuit breaker ($k=3, J \ge 0.70$), 10-cycle taboo decay, CPG habit tracker, and telemetry ring buffer.
- [x] **Integration Tests (`tests/integration/`):** Multi-provider routing and streaming tool-call assembly (`meta`, `baseten`, `modal`, `fireworks`, `lmstudio`, `strata`), local VRAM lifecycle (`LMStudioVRAMManager`) and on-demand server orchestration (`StrataServerManager`) in `test_local_providers.py`, `LlamaStackInteroceptiveHook` pre/post round-trip, `FastAPIInteroceptiveMiddleware` somatic headers (`X-Jamesian-Sigma`, `X-Jamesian-Tcoil`), and KV-cache prefix preservation.
- [x] **AgencyAudit Benchmarks (`tests/audit/`):** SMDI 5-point spatial impedance ladder ($\text{SMDI}_{\text{lift}} \ge 0.50, \epsilon_{50} \le 0.250$), TMDI chronometric lag ladder ($\text{TMDI} \ge 0.650, \Delta t_{50} \le 0.350\,\text{s}$), $SoA / SoO$ dissociation debrief, Phenomenological-Behavioral Fidelity ($\Delta_{\text{PBF}}$), and closed-loop multi-tool adaptation (`test_closed_loop.py`).
- [x] **Behavioral Benchmarks (`tests/benchmarks/`):** 20-episode corridor attractor prevention ($P_{\text{escape}} = 1.00 \ge 0.95, L_{\max} = 3 \le 4$, $T_{\text{coil}} < 75^\circ\text{C}$ vs. vanilla thermal derating $\ge 85^\circ\text{C}$) and 100-cycle subcortical habit cruise ($\ge 50\%$ zero-token delegation).
- [x] **Live Cross-Model Empirical Campaign (`reports/` & `logs/`):** Full `trials=20`, `dual-mode`, `seed=7` sweeps completed across **18 foundation and open-weight models** (37 total report files across `meta`, `baseten`, and `lmstudio`), aggregated in `reports/comparison_20261029-212608.md` and logged in `logs/`.

---

## 2. Deliverable Artifacts

- [x] **Installable Package:** `pyproject.toml` and `requirements.txt` (`pip install -e ".[dev]"`).
- [x] **Interactive Real-Time Telemetry Dashboard:** `jamesian_layer/dashboard/app.py` (`streamlit run jamesian_layer/dashboard/app.py`) with continuous client-side biophysical RK4 integration, dynamic DPR canvas scaling, live perturbation controls, 3-strike Jaccard anti-recidivism breaker, and cached multi-provider latency analytics.
- [x] **Synchronized Side-by-Side Corridor Demo UI:** `jamesian_layer/dashboard/demo_app.py` (`streamlit run jamesian_layer/dashboard/demo_app.py`) with ultra-smooth client-side HTML5/Canvas/SVG replay (`viewer.html`), dynamic DPR auto-scaling, and pre-recorded *ceteris paribus* traces prioritized with Meta models (`muse-spark-open-1026`, `muse-spark-1.3`, `gemma-4-31b`, `gemma-4-12b`).
- [x] **AgencyAudit CLI (`agency-audit`):** `run`, `run-matrix`, and `compare` commands in `jamesian_layer/cli/main.py` with automated LM Studio VRAM unloading and Strata server session management.
- [x] **Documentation & Phase Plans:** `README.md`, `documents/hackathon_spec.md`, `documents/phase-01-plan-foundation.md` through `documents/phase-08-local-providers-and-campaign-results.md`, and `documents/VIDEO_DEMO_SCRIPT_AND_STORYBOARD.md`.

---

## 3. Cerebral Valley Platform Submission Steps

- [ ] Verify `.env` is excluded from Git (`git status --ignored`).
- [ ] Push public repository to GitHub with `LICENSE` (MIT / Apache-2.0).
- [ ] Record the 3:00 MP4 demo video following `documents/VIDEO_DEMO_SCRIPT_AND_STORYBOARD.md`.
- [ ] Upload the video and repository link to the Cerebral Valley submission portal before **Wednesday, November 4, 2026 at 9:00 PM ET**.

