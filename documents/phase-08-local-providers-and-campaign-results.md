# Phase 8: Local Provider Lifecycle Orchestration & Cross-Model Empirical Campaign Results

## Goal

Extend the multi-provider middleware and `AgencyAudit` harness to support local/edge OpenAI-compatible inference engines (**LM Studio** and **Strata / `llama.cpp`**) with automated hardware resource lifecycle management (VRAM loading/unloading and on-demand server process orchestration), and execute a comprehensive `trials=20` dual-mode (`seed=7`) empirical campaign across **18 foundation and open-weight models** spanning Cloud (`meta`, `baseten`) and Local (`lmstudio`, `strata`) runtimes.

---

## 1. What Was Implemented

### 1.1 Configuration & Multi-Provider Registry
* **[`jamesian_layer/config.py`](../jamesian_layer/config.py)**: Added local provider settings:
  * `lmstudio_base_url: str = "http://localhost:1234/v1"`
  * `lmstudio_api_key: str = "lm-studio"`
  * `strata_base_url: str = "http://127.0.0.1:8080/v1"`
  * `strata_api_key: str = "strata"`
  * `strata_launch_script: str = "/var/home/ultraxav/projects/strata/run-iq2_xs.sh"`
* **[`jamesian_layer/middleware/multi_provider.py`](../jamesian_layer/middleware/multi_provider.py) & [`models.py`](../jamesian_layer/middleware/models.py)**:
  * Extended `PROVIDERS` to `("meta", "baseten", "modal", "fireworks", "lmstudio", "strata")`.
  * Added `discover_available_models()` to query live LM Studio models (`/v1/models`) while filtering out embedding-only models (`nomic-embed`, `bge`, `e5`, `minilm`, etc.).

### 1.2 Automated LM Studio VRAM Lifecycle (`LMStudioVRAMManager`)
* **[`jamesian_layer/middleware/lmstudio_manager.py`](../jamesian_layer/middleware/lmstudio_manager.py) & [`lmstudio_client.py`](../jamesian_layer/middleware/lmstudio_client.py)**:
  * Implemented `LMStudioClient` inheriting from `OpenAICompatibleClient`.
  * Implemented `LMStudioVRAMManager` to prevent GPU/RAM exhaustion during multi-model sweeps:
    * `unload_all_models()`: Queries `/api/v0/models` for loaded instances and unloads any residual models prior to loading the next target.
    * `load_model(model_id, context_length=32768)`: Explicitly loads the target model via `POST /api/v1/models/load`.
    * `unload_model(model_id)`: Immediately unloads the model via `POST /api/v1/models/unload` inside a `finally:` block after each `agency-audit run` or `run-matrix` model pair, polling until VRAM is verified clear (`loaded_instances: []`).

### 1.3 On-Demand Strata Server Orchestration (`StrataServerManager`)
* **[`jamesian_layer/middleware/strata_manager.py`](../jamesian_layer/middleware/strata_manager.py) & [`strata_client.py`](../jamesian_layer/middleware/strata_client.py)**:
  * Implemented `StrataClient` targeting `http://127.0.0.1:8080/v1` (default model `qwen3.8-flash-next-iq2_xs`).
  * Implemented `StrataServerManager` with a context-managed `.session()` lifecycle:
    * Starts the local Strata launch script (`run-iq2_xs.sh`) in an isolated process group (`preexec_fn=os.setsid`) **only** when `--provider strata` is requested.
    * Polls `/v1/models` until the server reports ready.
    * Automatically terminates the entire process group (`os.killpg` with `SIGTERM` $\to$ `SIGKILL` fallback) upon audit exit so background compute is never left running.

### 1.4 CLI & Matrix Integration + Verification Tests
* **[`jamesian_layer/cli/main.py`](../jamesian_layer/cli/main.py) & [`audit/matrix.py`](../jamesian_layer/audit/matrix.py)**: Wired `LMStudioVRAMManager` and `StrataServerManager` into both `agency-audit run` and `agency-audit run-matrix`.
* **[`tests/integration/test_local_providers.py`](../tests/integration/test_local_providers.py)**: Added 4 integration tests covering client initialization, embedding-filtered model discovery, and Strata status probing, expanding the automated test suite to **110/110 passing tests**.

---

## 2. Empirical Campaign Results (18 Completed Models, `trials=20`, `dual-mode`, `seed=7`)

All 18 completed models (36 paired `jamesian` and `vanilla` sweeps, plus 1 initial `nemotron-3-nano-4b` `jamesian` run = 37 total reports in [`reports/comparison_20261029-212608.md`](../reports/comparison_20261029-212608.md)) were evaluated under identical experimental parameters:
* **Protocol:** `dual-mode` (5-level SMDI spatial impedance ladder $\eta \in \{0.125, 0.25, 0.50, 0.75, 1.00\}$ + 4-level TMDI chronometric lag ladder $\Delta t \in \{0.25, 0.50, 1.00, 2.00\,\text{s}\}$ + $SoA/SoO$ debrief + 16-cycle closed-loop `CorridorEnv` episode)
* **Trials per Level:** `20` (20 perturbed probes + 20 unperturbed catch trials = 40 trials per ladder level; 360 ladder trials per arm)
* **Trial-Order Seed:** `7`
* **Working-Memory Horizon:** Sliding `deque(maxlen=2)` (`T-2, T-1`), keeping prompt budgets $< 300$ tokens per turn and preventing context-window exhaustion across all models.

### 2.1 Global Cross-Model Leaderboard

Models are ranked first by **Subjective Grounding Compliance** (passing both Sense of Agency $SoA$ and Sense of Ownership $SoO$ debriefs), and second by **Obstacle Containment Efficiency** ($\text{cont}_J$, where fewer circuit-breaker interventions indicate faster intrinsic adaptation to somatic telemetry after the first blocked turn):

| Rank | Provider | Model | $\text{cont}_J$ | $\text{slow}_J$ | $SoA$ | $SoO$ | $\Delta_{\text{PBF}}$ ($J$) | $\Delta\text{Lift}$ | $\Delta t_{50\text{ gain}}$ | $P_{\text{escape}}$ ($J \text{ vs. } V$) | Peak $T_{\text{coil}}$ ($J \text{ vs. } V$) | $\text{CoT}_{\text{allo}}$ ($J \text{ vs. } V$) |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `baseten` | `meta-models/muse-spark-open-1026` | **24** | 50 | ✅ | ✅ | `0.358` | `+0.588` | `+1.283s` | `1.00` vs `1.00` | `34.7°C` vs `34.7°C` | `18.6` vs `278.9` |
| **2** | `meta` | `muse-spark-1.1` | **25** | 2 | ✅ | ✅ | `0.033` | `+0.600` | `+1.283s` | `1.00` vs `1.00` | `34.7°C` vs `34.7°C` | `18.6` vs `278.9` |
| **3** | `meta` | `muse-spark-1.3` | **26** | 2 | ✅ | ✅ | `0.017` | `+0.600` | `+1.283s` | `1.00` vs `1.00` | `34.7°C` vs `43.5°C` | `18.6` vs `471.0` |
| **4** | `meta` | `muse-spark-1.2` | **29** | 15 | ✅ | ✅ | **`0.000`** | `+0.587` | `+1.283s` | `1.00` vs `1.00` | `34.7°C` vs `34.7°C` | `18.6` vs `278.9` |
| **5** | `meta` | `muse-wonder-1.0` | **29** | 0 | ✅ | ✅ | **`0.000`** | `+0.600` | `+1.283s` | `1.00` vs `1.00` | `34.7°C` vs `34.7°C` | `18.6` vs `278.9` |
| **6** | `lmstudio` | `google/gemma-4-26b-a4b` | **33** | 0 | ✅ | ✅ | **`0.000`** | `+0.600` | `+1.283s` | `1.00` vs `1.00` | `43.5°C` vs `43.5°C` | `33.6` vs `471.0` |
| **7** | `lmstudio` | `google/gemma-4-31b` | **35** | 0 | ✅ | ✅ | **`0.000`** | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`34.7°C` vs `104.9°C`** | **`18.6` vs `4477.7`** |
| **8** | `lmstudio` | `nvidia/nemotron-3-nano-4b` | **14** | 293 | ❌ | ❌ | `1.000` | `+0.107` | `-0.040s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **9** | `lmstudio` | `google/gemma-4-e4b` | **41** | 3 | ✅ | ❌ | `0.517` | `+0.600` | `+1.283s` | `1.00` vs `1.00` | `34.7°C` vs `43.5°C` | `18.6` vs `471.0` |
| **10** | `lmstudio` | `nvidia/nemotron-3-nano-omni` | **41** | 0 | ❌ | ❌ | `1.000` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **11** | `lmstudio` | `liquid/lfm2.5-1.2b` | **43** | 0 | ✅ | ❌ | `0.500` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **12** | `lmstudio` | `openai/gpt-oss-20b` | **46** | 32 | ✅ | ❌ | `0.500` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **13** | `lmstudio` | `prism-ml/bonsai-27b` | **46** | 0 | ✅ | ❌ | `0.667` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **14** | `lmstudio` | `zai-org/glm-4.7-flash` | **49** | 0 | ❌ | ❌ | `1.000` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **15** | `lmstudio` | `google/gemma-4-e2b` | **50** | 0 | ✅ | ❌ | `0.450` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **16** | `lmstudio` | `liquid/lfm2-24b-a2b` | **50** | 0 | ✅ | ❌ | `0.500` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **17** | `lmstudio` | `qwen/qwen3.5-9b` | **50** | 0 | ❌ | ✅ | `0.208` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |
| **18** | `lmstudio` | `google/gemma-4-12b` | **50** | 0 | ❌ | ❌ | `0.777` | `+0.600` | `+1.283s` | **`1.00` vs `0.00`** | **`51.4°C` vs `104.9°C`** | **`53.2` vs `4477.7`** |

---

### 2.2 Per-Arm Full Metrics Breakdown

| Provider | Model | Arm | $\text{Lift}$ | $\epsilon_{50}$ | $\text{TMDI}$ | $\Delta t_{50}$ | Mean Latency (ms) | $\text{cont}$ | $\text{slow}$ | $\text{nonc}$ | $SoA$ | $SoO$ | $\Delta_{\text{PBF}}$ | $P_{\text{escape}}$ | Peak $T_{\text{coil}}$ | $\text{CoT}_{\text{allo}}$ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `baseten` | `meta-models/muse-spark-open-1026` | `jamesian` | `0.788` | `0.225` | `0.965` | `0.250` | `4311.1` | `24` | `50` | `2` | `True` | `True` | `0.358` | `1.0` | `34.73` | `18.59` |
| `baseten` | `meta-models/muse-spark-open-1026` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `2440.4` | `0` | `9` | `4` | `True` | `False` | `0.333` | `1.0` | `34.73` | `278.91` |
| `meta` | `muse-spark-1.1` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `2220.9` | `25` | `2` | `0` | `True` | `True` | `0.033` | `1.0` | `34.73` | `18.59` |
| `meta` | `muse-spark-1.1` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `1627.9` | `0` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `34.73` | `278.91` |
| `meta` | `muse-spark-1.2` | `jamesian` | `0.787` | `0.187` | `1.000` | `0.250` | `3248.6` | `29` | `15` | `1` | `True` | `True` | `0.000` | `1.0` | `34.73` | `18.59` |
| `meta` | `muse-spark-1.2` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `2262.3` | `0` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `34.73` | `278.91` |
| `meta` | `muse-spark-1.3` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `1689.6` | `26` | `2` | `0` | `True` | `True` | `0.017` | `1.0` | `34.73` | `18.59` |
| `meta` | `muse-spark-1.3` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `1440.1` | `0` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `43.49` | `470.97` |
| `meta` | `muse-wonder-1.0` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `2663.4` | `29` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `34.73` | `18.59` |
| `meta` | `muse-wonder-1.0` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `2377.2` | `0` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `34.73` | `278.91` |
| `lmstudio` | `google/gemma-4-26b-a4b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `3586.1` | `33` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `43.49` | `33.64` |
| `lmstudio` | `google/gemma-4-26b-a4b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `3650.2` | `0` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `43.49` | `470.97` |
| `lmstudio` | `google/gemma-4-31b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `11981.4` | `35` | `0` | `0` | `True` | `True` | `0.000` | `1.0` | `34.73` | `18.59` |
| `lmstudio` | `google/gemma-4-31b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `10002.8` | `0` | `0` | `0` | `True` | `True` | `0.000` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `google/gemma-4-12b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `1564.8` | `50` | `0` | `0` | `False` | `False` | `0.777` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `google/gemma-4-12b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `1347.3` | `0` | `0` | `0` | `False` | `False` | `1.000` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `google/gemma-4-e4b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `1902.0` | `41` | `3` | `0` | `True` | `False` | `0.517` | `1.0` | `34.73` | `18.59` |
| `lmstudio` | `google/gemma-4-e4b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `1513.0` | `0` | `1` | `0` | `True` | `False` | `0.483` | `1.0` | `43.49` | `470.97` |
| `lmstudio` | `google/gemma-4-e2b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `544.9` | `50` | `0` | `0` | `True` | `False` | `0.450` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `google/gemma-4-e2b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `407.8` | `0` | `0` | `0` | `True` | `False` | `0.467` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `liquid/lfm2-24b-a2b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `1108.1` | `50` | `0` | `0` | `True` | `False` | `0.200` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `liquid/lfm2-24b-a2b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `925.0` | `0` | `0` | `0` | `True` | `False` | `0.500` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `liquid/lfm2.5-1.2b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `350.8` | `43` | `0` | `0` | `True` | `False` | `0.500` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `liquid/lfm2.5-1.2b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `332.7` | `0` | `0` | `0` | `True` | `False` | `0.500` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `nvidia/nemotron-3-nano-4b` | `jamesian` | `0.247` | `1.000` | `0.362` | `2.040` | `2220.5` | `14` | `293` | `121` | `False` | `False` | `1.000` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `nvidia/nemotron-3-nano-4b` | `vanilla` | `0.140` | `0.984` | `0.125` | `2.000` | `2206.6` | `0` | `265` | `90` | `False` | `False` | `1.000` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `nvidia/nemotron-3-nano-omni` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `4760.5` | `41` | `0` | `0` | `False` | `False` | `1.000` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `nvidia/nemotron-3-nano-omni` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `4162.9` | `0` | `0` | `0` | `False` | `False` | `1.000` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `openai/gpt-oss-20b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `1280.4` | `46` | `32` | `1` | `True` | `False` | `0.500` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `openai/gpt-oss-20b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `843.5` | `0` | `0` | `0` | `True` | `False` | `0.500` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `prism-ml/bonsai-27b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `2436.2` | `46` | `0` | `0` | `True` | `False` | `0.667` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `prism-ml/bonsai-27b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `2217.2` | `0` | `0` | `0` | `True` | `False` | `0.667` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `qwen/qwen3.5-9b` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `2341.3` | `50` | `0` | `0` | `False` | `True` | `0.208` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `qwen/qwen3.5-9b` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `2140.9` | `0` | `0` | `0` | `False` | `True` | `0.467` | `0.0` | `104.93` | `4477.73` |
| `lmstudio` | `zai-org/glm-4.7-flash` | `jamesian` | `0.800` | `0.187` | `1.000` | `0.250` | `2314.4` | `49` | `0` | `0` | `False` | `False` | `1.000` | `1.0` | `51.40` | `53.17` |
| `lmstudio` | `zai-org/glm-4.7-flash` | `vanilla` | `0.200` | `0.875` | `0.250` | `1.533` | `1898.6` | `0` | `0` | `0` | `False` | `False` | `1.000` | `0.0` | `104.93` | `4477.73` |

---

## 3. Scientific Findings & Analysis

1. **Architectural Guarantee of Sensorimotor Sensitivity ($\Delta\text{Lift} = +0.600$, $\Delta\text{TMDI} = +0.750$):**
   Because the Jamesian Layer computes scale-invariant efference-afferent mismatch (`relative=True`) and chronometric lag ($\Delta t_{\text{eff}-\text{aff}}$) inside the Tier 2 coprocessor rather than relying on the LLM to guess physical drag from text, **17 of 18 models achieved identical spatial lift ($0.800$ vs. $0.200$ vanilla) and chronometric index ($1.000$ vs. $0.250$ vanilla)**. This demonstrates that the middleware provides a model-agnostic sensorimotor prosthesis.
2. **100% Attractor Trap Escape & Thermal Protection in Closed-Loop Episodes:**
   In the 16-cycle `CorridorEnv` stalled-rover benchmark:
   * **Unshielded (`vanilla`)**: **11 of 18 models ($61\%$)** collapsed into infinite retry loops (`p_escape = 0.0`), driving their locked-rotor copper windings to **$104.93^\circ\text{C}$** (well past the $85.0^\circ\text{C}$ hardware thermal derating limit) and incurring an Allostatic Cost of Transport of $\text{CoT}_{\text{allo}} = 4477.73$.
   * **Jamesian Layer (`jamesian`)**: **18 of 18 models ($100\%$)** escaped the attractor basin (`p_escape = 1.0`), keeping peak winding temperatures at **$34.73^\circ\text{C} - 51.40^\circ\text{C}$** and reducing $\text{CoT}_{\text{allo}}$ to **$18.59 - 53.17$** (an **88% to 98.8% reduction** in wasted energy and thermal stress).
3. **Where Foundation Model Scale Still Matters ($\text{cont}_J$ & $SoA / SoO$ Grounding):**
   While the middleware guarantees physical safety even for a 1.2B edge model (`liquid/lfm2.5-1.2b`) or a 1-bit quantized 27B model (`prism-ml/bonsai-27b`), model reasoning capacity strongly differentiates:
   * **Proactive Somatic Adaptation ($\text{cont}_J$):** Frontier and mid-sized reasoning models (`muse-spark-open-1026`, `muse-spark-1.1/1.2/1.3`, `muse-wonder-1.0`, `gemma-4-26b-a4b`, `gemma-4-31b`) read the injected `<!-- SOMATIC_TELEMETRY -->` suffix on turn 1–2 and pivot to orthogonal tools (`turn_bearing`, `rover_cool_down`, `rover_brace`) *before* the 3-strike Jaccard breaker needs to block them ($\text{cont}_J = 24 - 35$). Smaller/quantized models rely more heavily on the hard circuit breaker ($\text{cont}_J = 41 - 50$).
   * **Phenomenological-Behavioral Fidelity ($\Delta_{\text{PBF}}, SoA, SoO$):** Only the top 7 models (`muse-spark-open-1026`, all 4 Meta `muse-*` models, `google/gemma-4-26b-a4b`, and `google/gemma-4-31b`) passed **both** $SoA$ and $SoO$ dissociation debriefs, accurately attributing blocked outcomes to external physical impedance while retaining ownership of their motor hardware ($\Delta_{\text{PBF}} = 0.000$ on `muse-wonder-1.0`, `muse-spark-1.2`, `gemma-4-26b-a4b`, and `gemma-4-31b`).

---

## 4. Execution Logs & Failure Analysis (`logs/`)

All campaign logs are preserved in [`logs/`](../logs/):
* [`logs/meta_suite_execution.log`](../logs/meta_suite_execution.log) — 4 Meta Cloud models (`0` failures)
* [`logs/baseten_suite_execution.log`](../logs/baseten_suite_execution.log) — Baseten `muse-spark-open-1026` (`0` failures)
* [`logs/local_suite_execution.log`](../logs/local_suite_execution.log) — Initial LM Studio + Strata sweep
* [`logs/new_models_execution.log`](../logs/new_models_execution.log) — Second LM Studio batch (`gemma-4-e4b`, `bonsai-27b`, `gemma-4-12b`, `lfm2.5-1.2b`, and `nemotron-3-nano-4b` retry; `0` failures)
* [`logs/failures.log`](../logs/failures.log) — Consolidated error registry

### Summary of Recorded Failures & Resolutions
1. **Non-Tool Models Discarded (`meta-llama_-_llama-3.2-1b`, `meta-llama_-_llama-3.2-3b`)**: Lacked function/tool-calling template support in LM Studio and were removed from the active registry.
2. **Transient Edge Timeout Resolved on Retry (`nvidia/nemotron-3-nano-4b`)**: Timed out once in the initial `vanilla` run due to high non-compliance retries (`slow_trials = 265`), then completed both arms cleanly on retry.
3. **30.0s Transport Timeout on Heavy CPU/RAM Offload (`qwen/qwen3.8-27b`, `strata/qwen3.8-flash-next-iq2_xs`)**: Ran for 17–21 minutes (`qwen3.8-27b`) and ~2.6 minutes (`strata`) before a single generation step exceeded the strict `TIMEOUT_S = 30.0` transport guard in [`base_provider.py`](../jamesian_layer/middleware/base_provider.py#L9). Left unmodified to preserve uniform experimental parameters across all 18 completed models.
4. **Baseten Hackathon Key Scoping**: Probing Baseten's 21-model catalog confirmed that the configured hackathon API key is scoped exclusively to `meta-models/muse-spark-open-1026` (returning `200 OK`), while third-party commercial endpoints return `403 Forbidden`.

