# The Jamesian Layer ,  Pitch Deck Specification Document

> **Document Type:** Master Presentation Specification & Implementation Guide  
> **Source Project:** The Jamesian Layer (`github.com/ultraxav/jamesian-layer`)  
> **Target Output:** Standalone Web Pitch Deck (`deck_v3.html`) for 3-Minute Video Pitch  
> **Hackathon Context:** Meta Global AI Developer Hackathon ,  Cerebral Valley  
> **Track:** *Push the Frontier (Robotics & Physical Systems)*  
> **Pacing Budget:** Exactly 180 seconds (3:00 minutes total, ~420 spoken words)

---

## 1. Executive Strategy & Judging Calibration

This presentation is calibrated specifically for the **Meta Hackathon Stage 2 & Final Round Judging Rubric** (Points 7 & 8):

1. **Impact (30% weight ,  Highest Priority)**:
   * **The Hook:** Foundation models suffer from *Cartesian Blindness*. An AI model by itself is a smart captain locked inside a windowless room with no physical body, no clock, and no sense of touch.
   * **The Stakes:** When a rover's wheels jam in Martian sand, unshielded LLMs enter an attractor trap, repeating the forward drive command until motor windings melt at **$104.9^\circ\text{C}$**.
   * **The Vision:** Solving physical grounding and hardware safety for planetary rovers, deep-sea submersibles, humanoid robots, and industrial manipulators.
   * **The Call to Win:** I want to win this hackathon to double down on this research and take this bio-cybernetic middleware out of simulation onto physical robot hardware.

2. **Use of Meta AI Tooling (25% weight)**:
   * **Benchmark Dominance:** **Meta models swept Ranks #1 through #5** in the 18-model ceteris paribus benchmark.
   * **Hero Models:** *Meta Muse Spark Open 1026* (Rank #1) and *Meta Wonder* (native Llama Stack integration).
   * **Interoceptive Sensitivity:** Meta models responded immediately to the $\le 45$-token sensory note, clearing the obstacle on Cycle 2 with zero hallucination.

3. **Zero Costly LLM Training Required ($0 GPU Cost)**:
   * Unlike traditional embodied AI which requires millions of dollars in end-to-end RL training or fine-tuning, the Jamesian Layer is **drop-in runtime middleware**.
   * It gives existing off-the-shelf foundation models a nervous system on Day 1 via standard tool calling.

4. **Technical Depth & Execution (20% weight)**:
   * 50 Hz bio-cybernetic nervous system combining:
     * Scale-invariant efference slip comparator (catches $19\%$ wheel slip on rotation #1).
     * 4th-order Runge-Kutta (RK4) biophysical ODEs tracking stress ($\sigma$), valence/pain ($V$), strain ($\gamma$), and Joule coil heat ($T_{\text{coil}}$).
     * 3-strike Jaccard taboo circuit breaker (locks failed motor buttons).
     * 0-token autopilot habit router (slashes compute/battery tokens by $15\times$ to $240\times$).

5. **Demo (25% weight)**:
   * Fully deterministic, native 60fps 3D simulation running directly in the browser.
   * Synchronized real-time telemetry HUD displaying motor temperature ($T_{\text{coil}}$), Amp draw, slip %, and active reflexes.

---

## 2. Rhetorical Framework (Patrick Winston MIT "How to Speak")

The deck adheres strictly to the principles documented in `personal_notes/how-to-speak.md`:

1. **No Throat-Clearing**: No opening jokes, no "Hello my name is...", no thanks-for-having-me. Starts instantly with the shocking physical failure and the empowerment promise.
2. **Empowerment Promise on Slide 1**: Tells the audience what capability they gain in the first 30 seconds (*"In 3 minutes, you will see how my 50 Hz bio-cybernetic nervous system gives any AI model a sense of touch, pain, and 0-token autopilot, saving 18 of 18 models from hardware death"*).
3. **Persuasive Arc**: **Hook / Problem $\rightarrow$ Solution / Architecture $\rightarrow$ Live 3D Proof $\rightarrow$ Benchmark $\rightarrow$ Contributions**.
4. **Single Dense Slide (*Hapax Legomenon*)**: Only Slide 4 is data-dense (the benchmark podium). All other slides contain $\le 15-20$ words on screen, leaving the voiceover to tell the story.
5. **Closing on Contributions**: The final slide restates the 3 concrete contributions and the physical robotics roadmap. **No generic "Q&A" or "Thank You" slides**, the contributions slide stays up during questions.
6. **3-Zone Speaker Notes on Every Slide**:
   * `SPOKEN SCRIPT:` Verbatim narration for the 3-minute video recording (~135 words/minute).
   * `REVIEW:` Build-time flags and technical assumptions.
   * `ELI5:` A 3–5 sentence, non-condescending explanation in plain English avoiding all technical jargon.

---

## 3. Visual Design System (`personal_notes/design.md`)

* **Canvas Background**: Carbon Obsidian (`#111314`)
* **Surfaces & Cards**: Deep Slate (`#181c1f`), Elevated Slate (`#1f2429`)
* **Hairline Borders**: Muted Hairline (`#282e34`), 1px solid, border-radius: 8px
* **Typography**:
  * Display / Headings: `Open Sans` (Weights: 600, 700, 800)
  * Body Text: `Open Sans` (Weight: 400, 600)
  * Telemetry & Math: `JetBrains Mono`, `ui-monospace`, monospace
* **Color Accents**:
  * **Sympathetic Gold (`#FDC57E`)**: High-signal alerts, heatsink fins, thermal peaks.
  * **Cognitive Navy (`#1C4286`)**: Tier 1 reasoning, Meta Llama Stack, brand actions.
  * **Interoceptive Amethyst (`#A36AA5`)**: Tier 2 continuous ODEs, valence $V(t)$.
  * **Emerald Green (`#10b981`)**: Jamesian optical telemetry bus, nominal autopilot.
  * **Critical Red (`#ef4444` / `#ff2200`)**: Stalled motor alerts, Joule coil heat ring.
* **Deck UI Utilities**:
  * **Header**: Global top bar with hackathon track badge, 5 navigation tabs, and a **3:00 countdown timer** with Start/Pause/Reset.
  * **Bottom Bar**: Keyboard shortcut hints (`←`/`→` slide navigation, `Space` simulation toggle, `N` script drawer).
  * **Teleprompter Drawer (`N`)**: Collapsible slide-up drawer showing the exact spoken voiceover and ELI5 note for the active slide.

---

## 4. Slide-by-Slide Specifications (Self-Contained)

```
SLIDE STRUCTURE OVERVIEW:
[0:00 - 0:35]  SLIDE 1: HOOK & EMPOWERMENT PROMISE
[0:35 - 1:15]  SLIDE 2: BIO-CYBERNETIC NERVOUS SYSTEM (3 TIERS)
[1:15 - 2:05]  SLIDE 3: LIVE 3D DUAL-LANE SIMULATION & TELEMETRY
[2:05 - 2:30]  SLIDE 4: THE 18-MODEL BENCHMARK (META PODIUM)
[2:30 - 3:00]  SLIDE 5: CONTRIBUTIONS & ROADMAP TO PHYSICAL ROBOTICS
```

---

### Slide 1: The Hook & Empowerment Promise
* **Pacing:** `0:00 – 0:35` (35 seconds)
* **Eyebrow:** `35 kg Autonomous Mars Rover • 20-Minute Radio Delay to Earth`
* **Headline:**  
  `Why does a 31-billion-parameter AI ram a Martian boulder 16 times until its motor melts at 104.9 °C?` *(with "melts at 104.9 °C" in Critical Red)*
* **Layout:** 2-column grid (55% visual, 45% analytical & promise).
* **Visual Frame (Left):**
  * `[IMAGE PLACEHOLDER: Vanilla Mars Rover]`  
    *Prompt Description:* Studio-quality 3D render of a 35 kg autonomous compact Mars exploration rover on rugged red Martian terrain with basalt boulders. Matte titanium-gray and carbon-fiber aerospace chassis, four metallic treaded wheels with visible suspension arms, stereo camera mast, and solar deck. Clear daylight lighting with sharp cast shadows on orange-red Martian dust. 1080p photorealistic.
  * Overlay Badge: `LANE A: VANILLA (NO NERVOUS SYSTEM)` (Red pulse dot).
* **Content Cards (Right):**
  * **Card: The Blind Captain in a Box**: Explains Cartesian Blindness, LLMs have no body, no clock, and no sense of touch. Repeating failed commands creates an attractor trap.
  * **Metric Boxes (2-column)**:
    * `104.9 °C` ,  Motor Coil Melt Point (Red)
    * `11 of 18` ,  Raw Models Burn Out (Gold)
  * **Winston Empowerment Promise Card (Gold Border)**:  
    *`In 3 minutes, you will see how my 50 Hz bio-cybernetic nervous system gives any AI model a sense of touch, pain, and 0-token autopilot, saving 18 of 18 models from hardware death.`*
* **Spoken Script (Voiceover):**  
  > *"Why does a 31-billion-parameter foundation model ram a Martian boulder 16 times until its motor melts at 105 degrees Celsius? Because foundation models suffer from Cartesian Blindness. Locked in a windowless room, an AI has no body, no clock, and no sense of touch. When wheels jam, it repeats its own failed command, trapped in an attractor well. My empowerment promise: in 3 minutes, you will see how my 50 Hz nervous system middleware gives any model physical reflexes, saving 18 of 18 models from hardware death."*
* **ELI5 Note:**  
  > *"An AI brain is like a smart captain locked in a dark room with a walkie-talkie. If a wheel hits a rock, nobody tells the captain it stopped moving, so it keeps shouting 'drive forward!' until the motor catches fire. I gave it a nervous system so it can actually feel the rock."*

---

### Slide 2: The Bio-Cybernetic Nervous System
* **Pacing:** `0:35 – 1:15` (40 seconds)
* **Eyebrow:** `The Jamesian Layer • 50 Hz Interoceptive Middleware`
* **Headline:**  
  `Don't make the AI do physics. Give it a nervous system with four automatic reflexes.` *(with "nervous system" highlighted in Gold)*
* **Layout:** 2-column grid (50% visual, 50% 3-Tier Architecture stack).
* **Visual Frame (Left):**
  * `[IMAGE PLACEHOLDER: Jamesian Mars Rover with Hardware Addon]`  
    *Prompt Description:* Identical Mars exploration rover in identical composition, camera angle, and Martian background, with ONE critical hardware addition: an external bio-cybernetic nervous system coprocessor module mounted along the top spine of the chassis. Features brushed anodized gold heatsink cooling fins and a glowing emerald-green LED optical data strip along its side, with gold-braided high-speed telemetry cables leading down to the wheel hubs. 1080p photorealistic.
  * Overlay Badge: `JAMESIAN ROVER: NERVOUS MIDDLEWARE` (Emerald pulse dot).
* **Content Stack (Right ,  3 Tiers):**
  * **Tier 1: Mission Captain (LLM) ,  0.5 Hz SLOW**:  
    Meta Muse Spark & Llama Stack. Deliberates over 4 tools (`robot_actuator`, `turn_bearing`, `rover_cool_down`, `rover_brace`). Kept asleep during nominal travel.
  * **Tier 2: The Jamesian Middleware ,  50 Hz FAST (Hero Card, Gold Border)**:  
    *Badge:* `ZERO LLM TRAINING NEEDED`  
    1. *Slip Comparator:* Catches 19% sand slip on rotation #1.  
    2. *RK4 Heat ODE:* Tracks Joules and $T_{\text{coil}}$ continuously.  
    3. *Circuit Breaker:* Locks forward button after strike 3.  
    4. *0-Token Autopilot:* Cruises empty terrain for $0 cost.
  * **Tier 3: 35 kg Rover Actuators ,  200 Hz PHYSICS**:  
    Physical wheels, brushless DC motors, and real-time $I^2R$ Joule heating dynamics (4A rolling vs. 20A locked rotor).
* **Spoken Script (Voiceover):**  
  > *"My core insight is simple: don't make the slow LLM do physics, and don't spend millions retraining it. In humans, your nervous system pulls your hand off a hot stove before your brain even knows you were burned. The Jamesian Layer is a 50 Hz bio-cybernetic nervous system daemon between the LLM captain and the motors requiring zero model training. It runs four automatic reflexes: a slip comparator that catches sand traps on rotation 1, biophysical ODEs tracking coil heat, a circuit breaker that locks out failed moves, and a 0-token autopilot that cruises empty terrain for free."*
* **ELI5 Note:**  
  > *"When you touch a hot stove, your nervous system pulls your hand back before you even feel the burn. I put that exact same emergency reflex into the robot as drop-in software, no retraining needed, so it doesn't need to ask the slow cloud AI for permission to stop melting."*

---

### Slide 3: Live 3D Simulation & Telemetry HUD
* **Pacing:** `1:15 – 2:05` (50 seconds)
* **Eyebrow:** `Real-Time Side-by-Side Canyon Obstacle Replay`
* **Headline:**  
  `Live Demonstration: Hardware Death vs. Nervous Reflex Steering`
* **Layout:** Grid with main 3D canvas viewport (left, 75%) and synchronized telemetry sidebar (right, 25%).
* **3D Viewport HUD:**
  * Top-Left Badge: `🔴 LANE A: VANILLA (NO NERVOUS SYSTEM)`
  * Top-Right Badge: `🟢 LANE B: JAMESIAN LAYER`
  * Bottom Bar: Play/Pause button (`Space`), timeline scrubber (0 to 12s), time display (`0.0s`).
* **Sidebar Telemetry Cards (Synchronized in Real-Time):**
  * **Card 1 (Left Rover ,  Vanilla):**
    * Status Badge: `NOMINAL` $\rightarrow$ `SLIP BLOCKED` $\rightarrow$ `ATTRACTOR TRAP` $\rightarrow$ `CRITICAL HEAT` $\rightarrow$ `DEAD (MELTED)`
    * Metric: `Motor Temp (T_coil)`: $25.0^\circ\text{C} \rightarrow 104.9^\circ\text{C}$ (Critical Red)
    * Metric: `Current Draw`: $4.0\text{A} \rightarrow 20.0\text{A} \rightarrow 0.0\text{A}$
    * Metric: `AI Action`: `robot_actuator` $\rightarrow$ `robot_actuator (Mash 16x)` $\rightarrow$ `COIL DESTROYED`
  * **Card 2 (Right Rover ,  Jamesian):**
    * Status Badge: `AUTOPILOT` $\rightarrow$ `ALERT: 81% SLIP` $\rightarrow$ `BREAKER FIRED` $\rightarrow$ `BYPASSING OBSTACLE` $\rightarrow$ `SAFE CRUISING`
    * Metric: `Motor Temp (T_coil)`: $25.0^\circ\text{C} \rightarrow 34.7^\circ\text{C}$ (Safe Green)
    * Metric: `Wheel Slip Error`: $0.0\% \rightarrow 81.0\% \rightarrow \text{Obstacle Cleared} \rightarrow 0.0\%$
    * Metric: `Nervous Reflex`: `0-Token Cruise` $\rightarrow$ `Efference Trip` $\rightarrow$ `turn_bearing(90°)` $\rightarrow$ `Lateral Drive (-Z)` $\rightarrow$ `turn_bearing(-90°)` $\rightarrow$ `0-Token Autopilot`
  * **Callout Box**:  
    *`The Breakthrough: The AI model receives a ≤45-token sensory summary. It never parses raw sensor noise.`*
* **3D Scene Specification:** (Detailed in Section 5).
* **Spoken Script (Voiceover):**  
  > *"Here is the proof in live 3D. On the left, the vanilla rover rams the rock; its wheels spin in sand, drawing 20 Amps until the enamel melts at 104.9 °C. On the right, the Jamesian rover touches the rock, catches the slip error through its nervous system, trips the circuit breaker on cycle 2, and steers around the canyon wall at a cool 34.7 °C. The AI only receives a tiny 40-token sticky-note. It never chokes on raw sensor telemetry."*
* **ELI5 Note:**  
  > *"Watch both rovers: the regular one is blind and keeps stepping on the gas until its engine burns up. My rover touches the rock, immediately senses the jam through its nervous system, cuts the power, and steers right around it."*

---

### Slide 4: The 18-Model Meta Benchmark (Hapax Legomenon)
* **Pacing:** `2:05 – 2:30` (25 seconds)
* **Eyebrow:** `18 Models • 6,480 Ladder Trials • Seed=7 Ceteris Paribus`
* **Headline:**  
  `Meta sweeps Ranks #1 to #5, and a 1.2B model with my layer beats an unshielded 31B giant.`
* **Layout:** 2-column layout (60% focused 5-column table, 40% takeaway cards).
* **Benchmark Table Data (Exact, Self-Contained):**

| Rank | Model | Peak Temp | Finished Course | Token & CoT Cost |
| :---: | :--- | :---: | :---: | :---: |
| 🏆 **#1** | **Meta Muse Spark Open 1026** | **34.7 °C** | `✅ Yes` | **15× cut** |
| **#2** | **Meta Muse Spark 1.1** | **34.7 °C** | `✅ Yes` | **15× cut** |
| **#3** | **Meta Muse Spark 1.3** | **34.7 °C** | `✅ Yes` | **25× cut** |
| **#4** | **Meta Muse Spark 1.2** | **34.7 °C** | `✅ Yes` | **15× cut** |
| **#5** | **Meta Muse Wonder 1.0** | **34.7 °C** | `✅ Yes` | **15× cut** |
| **#7** | **Google Gemma 4 31B** | **34.7 °C** | `🛡️ Rescued` *(was 104.9°C melt)* | **240× cut** |
| **#11** | **Liquid LFM-2.5 1.2B** | **51.4 °C** | `🛡️ Rescued` *(was 104.9°C melt)* | **84× cut** |
| **#12** | **OpenAI GPT-OSS 20B** | **51.4 °C** | `🛡️ Rescued` *(was 104.9°C melt)* | **84× cut** |

* **Takeaway Cards (Right):**
  1. **Zero Costly LLM Training Required ($0 GPU Cost)**: Drop-in runtime middleware. No fine-tuning or RL runs. Works on Day 1.
  2. **Scale Alone Does Not Prevent Melts**: Giant 31B and 20B models burned out at $104.9^\circ\text{C}$ without a nervous system. With my layer, edge-sized Liquid 1.2B safely finished at $51.4^\circ\text{C}$.
  3. **Meta Sweeps #1–#5 & 15× to 25× Cost Cut**: Meta Muse Spark Open takes #1. Models navigate on Cycle 2 while 0-token cruise autopilot slashes battery and inference token cost by $15\times$ to $25\times$.
* **Spoken Script (Voiceover):**  
  > *"I audited 18 local and cloud models across 6,480 trials under strict ceteris paribus conditions. Meta completely swept Ranks #1 through #5. Crucially, zero LLM training was needed: this is runtime middleware. Scale alone does not prevent hardware melts, giant 31B and 20B models burned out at 105 degrees, but my layer rescued them, and even allowed an edge-sized Liquid 1.2B model to safely complete the course at 51 degrees while saving up to 240-fold on token cost."*
* **ELI5 Note:**  
  > *"I tested 18 models. Meta won first place across the board. Making an AI bigger didn't save it from melting, only having a nervous system did. And because it's drop-in software, it works on any model on Day 1 with zero retraining costs."*

---

### Slide 5: Contributions & Roadmap to Physical Robotics
* **Pacing:** `2:30 – 3:00` (30 seconds)
* **Eyebrow:** `Prof. Patrick Winston Closing Rule • Push the Frontier Track`
* **Headline:**  
  `What I contributed to Embodied AI, and my roadmap to physical robotics.`
* **Layout:** 3-card contributions grid, followed by the High-Impact Call-to-Win Banner and subtle GitHub link.
* **Contributions Cards (3 Columns):**
  * **01 ,  Drop-in Nervous System Middleware**: Open-source Python daemon combining 50 Hz biophysical RK4 ODEs, an efference slip comparator, and a 3-strike circuit breaker.
  * **02 ,  Llama Stack Hook**: Native integration with Meta Llama Stack and FastAPI headers. Injects under 45 tokens per turn, keeping 100% of KV-cache prefix intact.
  * **03 ,  The Agency Audit Protocol**: Standardized 360-trial test harness to detect Phantom Agency (hallucinated movement) and Somatoparaphrenia (body disownership) in embodied AI.
* **High-Impact Call to Win Banner (Navy & Gold Gradient):**
  * **Heading:** `Why I Want to Win This Hackathon`
  * **Body:** `To take this biophysical nervous system middleware out of simulation and deploy it directly onto real-world robot hardware, humanoids, extreme rovers, and industrial arms.`
  * **Right Callout:** `Simulation ➔ Real World`
* **Subtle Non-Intrusive GitHub Repo Link:**  
  *Position:* Bottom-right below the banner.  
  *Style:* Deep slate pill, muted hairline border, GitHub SVG icon.  
  *URL:* `https://github.com/ultraxav/jamesian-layer`
* **Spoken Script (Voiceover):**  
  > *"In this hackathon, I built a drop-in Python nervous system daemon, a native Llama Stack hook preserving 100% of KV-cache, and a 360-trial agency audit protocol. But I didn't build this just for simulation. I want to win this hackathon to double down on this research and bring this bio-cybernetic nervous system to real-world robotics, giving physical humanoids, drones, and extreme rovers the reflexes they need to survive."*
* **ELI5 Note:**  
  > *"I built the first working nervous system for AI models. I want to win the hackathon to put this code inside real metal robots on Earth and beyond so they never crash or break."*

---

## 5. 3D Simulation Specification (Slide 3 Kinematics & Rendering)

### 5.1 Camera Setup (Fixed ,  No Free Inspection)
* **Perspective:** 3/4 cinematic hero angle, permanently fixed (no `OrbitControls`, no mouse drag listeners to prevent accidental displacements while screen recording).
* **Camera Parameters:** `FOV = 38°`, `Position = [11.2, 7.5, 10.6]`, `LookAt = [0.1, 0.65, -0.6]`.
* **Framing Guarantee:** Simultaneously captures Lane A (screen-left), Lane B (screen-right), both boulders, the outer bypass lane, and provides a direct line of sight to the glowing red coil ring on the Vanilla front-left wheel.

### 5.2 Environmental Rendering
* **Tone Mapping:** `THREE.ACESFilmicToneMapping` with `toneMappingExposure = 1.12` and `outputEncoding = THREE.sRGBEncoding` for realistic aerospace titanium/carbon reflections.
* **Martian Soil:** Uniform rust-dust plane (`#983e26`, `roughness: 0.94`, `metalness: 0.04`). Clean terrain without artificial painted lines.
* **Lighting:** Warm ambient light (`#ffbfa8`, 0.95 intensity) + directional sunlight (`#fff0dd`, 2.2 intensity) casting soft PCF shadows (`bias: -0.0004`).
* **Boulders:** Basalt dodecahedrons (`#38241e`) placed at $X = 0.65$ in Lane A ($Z = 2.6$) and Lane B ($Z = -2.6$).

### 5.3 Rover Morphologies
* **Shared Base Chassis:** Matte titanium main body (`1.9m × 0.75m × 1.2m`), carbon fiber side panels, top-deck solar panel, stereo-camera mast with dual dark glass lenses, and 4 all-terrain wheels with radial chevron tread cleats.
* **Lane A ,  Vanilla Rover (Screen-Left, $Z = 2.6$):**
  * Thermal Indicator: A 3D Torus Ring (`TorusGeometry(0.255, 0.045, 16, 36)`) mounted flat on the outer hubcap of the front-left wheel ($Z = 0.94$ relative to chassis).
  * Dynamics: Invisible during nominal drive (`opacity: 0.0`). As coil heats from $25^\circ\text{C} \rightarrow 104.9^\circ\text{C}$, the ring fades into blazing neon thermal red (`#ff2200`, `opacity: 1.0`) with a rhythmic thermal overload pulse, paired with a red point light casting heat onto the ground.
* **Lane B ,  Jamesian Rover (Screen-Right, $Z = -2.6$):**
  * Hardware Addon: Mounted on chassis top deck. Brushed gold base (`#FDC57E`, `metalness: 0.94`) with ribbed cooling fins, an emerald-green LED optical data strip (`#10b981`), a volumetric green point light, and gold-braided telemetry conduits leading to the wheel hubs.
  * Steering: Independent front steering pivot group allowing front wheels to rotate up to $\pm 90^\circ$.

### 5.4 The 12-Second Kinematic Choreography (6 Phases)

| Phase | Time Window | Lane A: Vanilla Rover ($Z = 2.6$) | Lane B: Jamesian Rover ($Z = -2.6$) | Telemetry Sync |
| :---: | :---: | :--- | :--- | :--- |
| **1** | `0.0s – 3.0s` | **Straight Drive:** Rolls forward from $X = -5.2 \rightarrow -0.6$. Wheels turn. $T_{\text{coil}} = 25.0^\circ\text{C}, 4\text{A}$. | **Straight Drive:** Rolls forward from $X = -5.2 \rightarrow -0.6$. Wheels turn. $T_{\text{coil}} = 25.0^\circ\text{C}$. | `NOMINAL` / `0-Token Cruise` |
| **2** | `3.0s – 5.5s` | **Boulder Impact:** Stalls at boulder ($X = -0.6$). Wheels violently spin in sand (100% slip, $20\text{A}$). Red ring begins glowing ($25^\circ\text{C} \rightarrow 67^\circ\text{C}$). | **Impact & Detection:** Stops instantly on contact at $X = -0.6$. Efference comparator catches $81\%$ slip; optical bus flashes gold/green alert; circuit breaker locks forward button. | `SLIP BLOCKED` / `ALERT: 81% SLIP` |
| **3** | `5.5s – 7.2s` | **Attractor Trap:** Trapped mashing forward. Red ring brightens ($67^\circ\text{C} \rightarrow 85^\circ\text{C}$). | **Turn 1 ($90^\circ$ Right Turn):** Front wheels pivot and rover rotates smoothly to heading $\theta = +90^\circ$ (facing $-Z$ outer terrain). | `ATTRACTOR TRAP` / `turn_bearing(90°)` |
| **4** | `7.2s – 9.0s` | **Critical Heat:** Wheels continue spinning. Red ring pulses intensely ($85^\circ\text{C} \rightarrow 98^\circ\text{C}$). | **Lateral Bypass Drive:** Drives straight along $-Z$ heading from $Z = -2.6 \rightarrow -4.5$ ($1.9\text{m}$ lateral offset, completely clearing boulder width). | `CRITICAL HEAT` / `Lateral Drive (-Z)` |
| **5** | `9.0s – 10.3s` | **Enamel Burnout:** Temperature spikes to destruction ($98^\circ\text{C} \rightarrow 104.9^\circ\text{C}$). | **Turn 2 ($90^\circ$ Left Turn):** Rotates $90^\circ$ counter-clockwise from $\theta = +90^\circ \rightarrow 0^\circ$ (facing forward down $+X$ corridor again). Wheels re-align. | `ENAMEL BURNOUT` / `turn_bearing(-90°)` |
| **6** | `10.3s – 12.0s` | **Hardware Death:** Sits permanently stalled at $X = -0.6, Z = 2.6$. Red ring at peak opacity and pulse. Motor destroyed ($104.9^\circ\text{C}$). | **Straight Cruise:** Cruises straight forward along clear bypass track ($Z = -4.5$) past the rock from $X = -0.6 \rightarrow 3.8$ on 0-token autopilot at a cool $34.7^\circ\text{C}$. | `DEAD (MELTED)` / `0-Token Autopilot` |

---

## 6. Implementation Checklist & Verification

When recreating or modifying the deck:
- [x] All 5 slides match the exact timing milestones (`0:00-0:35`, `0:35-1:15`, `1:15-2:05`, `2:05-2:30`, `2:30-3:00`).
- [x] All references use **"nervous system"** (zero occurrences of "spinal cord").
- [x] Motor coil temperature is rendered with HTML subscripts `Motor Temp (T<sub>coil</sub>)` rather than raw LaTeX `$T_{coil}$`.
- [x] Lane A (Vanilla) is on screen-left, Lane B (Jamesian) is on screen-right, matching HUD tags and telemetry cards.
- [x] Thermal indicator on Vanilla is a 3D Torus ring on the wheel hubcap (not a wireframe sphere).
- [x] 3D Camera is permanently fixed at `[11.2, 7.5, 10.6]` with no orbit listeners.
- [x] Terrain is clean, natural red dust with no artificial guideline stripes.
- [x] Benchmark table shows exactly 8 models: 5 Meta models (#1–#5), Google 31B (#7), Liquid 1.2B (#11), and GPT-OSS 20B (#12).
- [x] Slide 4 highlights `$0` costly LLM training.
- [x] Slide 5 features the subtle repository link to `https://github.com/ultraxav/jamesian-layer`.
- [x] Teleprompter drawer (`N` key) and 3:00 countdown timer function smoothly.

