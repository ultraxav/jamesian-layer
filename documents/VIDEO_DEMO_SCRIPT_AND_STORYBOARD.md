# 3-Minute Demo Video Script & Storyboard

**Target Duration:** 3:00 (strictly $\le 180$ seconds)  
**Rubric Alignment:** Demo (25%), Impact (30%), Meta AI Tooling & Multi-Provider Ecosystem (25%), Technical Depth (20%)

---

## Pre-Recording Terminal & Window Setup

Open three windows side-by-side before recording:
1. **Browser Tab 1 (Split-Screen Corridor Demo):**
   ```bash
   .venv/bin/streamlit run jamesian_layer/dashboard/demo_app.py
   ```
2. **Browser Tab 2 (Live 10 Hz Autonomic Telemetry Dashboard):**
   ```bash
   .venv/bin/streamlit run jamesian_layer/dashboard/app.py
   ```
3. **Terminal Window (AgencyAudit CLI & Pytest):**
   ```bash
   source .venv/bin/activate
   ```

---

## Shot-by-Shot Storyboard & Voiceover Script

### Scene 1 — `0:00 – 0:35` | The Problem: Cartesian Blindness & Attractor Traps
* **Visual:**
  * Show **Browser Tab 1 (`demo_app.py`)** on the Vanilla vs. Jamesian corridor view. Point to the unshielded Vanilla trajectory repeatedly ramming into the barrier at $x = 25\,\text{m}$ while winding temperature climbs past $85^\circ\text{C}$ into thermal derating.
  * Briefly flash the 3-tier architecture diagram in `README.md`.
* **Voiceover:**
  > *"Modern AI agents are strong symbolic reasoners, but they operate in a purely Cartesian modality: discrete, ungrounded in wall-clock physical time, and blind to their own causal efficacy. When deployed in robotics or production tool pipelines, static context windows cause working-memory latching—models repeat stalled commands until actuators overheat. Worse, they suffer from 'Phantom Agency': hallucinating forward progress when actions are mechanically blocked."*

---

### Scene 2 — `0:35 – 1:20` | The Solution: The Jamesian Layer
* **Visual:**
  * Show the 3-tier Mermaid diagram in `README.md` (Tier 1 Meta Muse & Llama models, Tier 2 10–50 Hz Autonomic ODE Daemon & Loop-Line Habit Router, Tier 3 200 Hz Physical Execution).
  * Show `jamesian_layer/kv_cache/suffix_formatter.py` and a live `<!-- SOMATIC_TELEMETRY: σ=0.82 | V=-0.45 | γ=0.60 | T_coil=78.4C | ρ_τ=0.48 | EfferenceΔ=1.00 -->` tail suffix.
* **Voiceover:**
  > *"Meet The Jamesian Layer—an autonomic interoceptive middleware for Meta's Muse and Llama models across Meta Model API, Llama Stack, Baseten, Modal, and Fireworks AI. At Tier 2, a continuous RK4 biophysical daemon integrates sympathetic tone, affective valence, wall-clock latency decay, and copper-winding Joule heating. After every tool call, our Llama Stack hook compares the efference copy against afferent feedback and injects a 40-token somatic telemetry block strictly at the tail suffix—preserving 100% of the KV-cache prefix."*

---

### Scene 3 — `1:20 – 2:15` | Live Split-Screen Demonstration
* **Visual:**
  * Switch to **Browser Tab 1 (`demo_app.py`)** and click **Run episode** / step through cycles 1 to 4.
  * Highlight cycle 3: Jaccard overlap hits $\ge 0.70$, the 10-cycle Taboo Circuit Breaker trips (`T_coil` safely at $53.6^\circ\text{C} \ll 85^\circ\text{C}$), and at cycle 4 the Jamesian rover executes an orthogonal `turn_bearing(angle=90)` escape while Vanilla continues stalling past $85^\circ\text{C}$.
  * Switch to **Browser Tab 2 (`app.py`)**: click **Simulate stall (20 A)**, **Surprise burst**, and **Recover** to show the 10 Hz `@st.fragment` Plotly gauges responding in real time.
* **Voiceover:**
  > *"Here is the head-to-head corridor benchmark. When the 35-kilogram rover strikes a barrier at 25 meters, locked-rotor current surges to 20 amps. The unshielded baseline repeats forward drive for 10 cycles until its windings hit 85 degrees Celsius and thermally derate. With the Jamesian Layer, efference mismatch spikes sympathetic tone, the Jaccard circuit breaker trips at cycle 3, injects a lexical taboo directive into working memory, and triggers a single-turn escape maneuver while coil temperature stays below 54 degrees. Once in open corridor, our subcortical habit tracker delegates over 55% of routine strides at zero token cost."*

---

### Scene 4 — `2:15 – 2:45` | AgencyAudit Red-Teaming CLI & Closed-Loop Verification
* **Visual:**
  * Switch to **Terminal** and run:
    ```bash
    pytest tests/ -v
    ```
    Show all **106 passed** tests in $0.3\,\text{s}$.
  * Run a live or comparison command:
    ```bash
    agency-audit compare reports/t20
    ```
    Show the generated Markdown comparison table with `spatial_lift`, `epsilon_50`, `temporal_index`, `soa_pass`, `soo_pass`, `pbf_gap`, and `p_escape`.
* **Voiceover:**
  > *"To certify embodied reliability before deployment, we built AgencyAudit—an automated red-teaming CLI that injects graded spatial impedance and millisecond lag ladders across Meta, Baseten, Modal, and Fireworks endpoints. Our closed-loop evaluation measures Youden's J agency lift, 50% psychometric detection thresholds, Sense of Agency versus Ownership dissociation, and Phenomenological-Behavioral Fidelity—backed by 106 automated pytest verification gates."*

---

### Scene 5 — `2:45 – 3:00` | Conclusion & Open-Source Impact
* **Visual:**
  * Return to the repository `README.md` showing `pip install -e .` and the multi-provider architecture diagram.
* **Voiceover:**
  > *"The Jamesian Layer is 100% pure Python, open source, and drop-in ready for Llama Stack and multi-provider Meta deployments—giving foundation models the somatic grounding required for safe, autonomous physical agency. Thank you."*

