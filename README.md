# The Jamesian Layer: Autonomic Interoceptive & Agency-Auditing Middleware for Foundation Models

[![Meta Hackathon](https://img.shields.io/badge/Meta%20Global%20AI%20Hackathon-Cerebral%20Valley-blue.svg)](https://cerebralvalley.ai)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Submission for the Meta Global AI Developer Hackathon (Co-hosted with Cerebral Valley)**  
> **Tracks:** Push the Frontier (Advanced AI, Robotics, Systems) & Indie Developer / Startup Track  
> **Target Bonus Awards:** *Best Build on Meta Open Weight Models* ($10,000) & *Best Agentic Use-Case* ($5,000)  
> **Empirical Validation Archive:** 88 longitudinal benchmark runs, 22,000 cognitive cycles across 11 foundation models (`v1`–`v7` in [`benchmark_evolution.csv`](file:///home/ultraxav/projects/jamesian_loop/benchmark_evolution.csv)).

---

## 1. Executive Summary & The Problem

Modern Foundation Models and Vision-Language-Action (VLA) agents operate in a purely **"Cartesian"** modality: they are discrete, turn-based, ungrounded in real wall-clock physical time, and blind to their own causal efficacy. In production agentic pipelines, this produces two pervasive failure modes:

1. **Recursive Attractor Traps (Infinite Retry Loops):**  
   When an external tool, API, or physical actuator fails, static context windows trigger working-memory latching ($T-2, T-1$). In empirical testing, ungrounded foundation models collapse into stationary attractor basins, burning API tokens on identical, repetitive commands with maximum streaks exceeding $40$ cycles.
2. **"Phantom Agency" (Hallucinated Causal Control):**  
   Agents cannot differentiate between an action that physically succeeded versus one that was silently blocked or dropped by the environment. In our baseline benchmarks, foundation models exhibited a **$54.5\%$ failure rate**, hallucinating downstream state transitions when tool calls were attenuated.

### The Solution: The Jamesian Layer
Grounded in the functional computational phenomenology of William James (1884, 1890) and the comparator model of sensorimotor agency (Sato & Yasuda, 2005; Gallagher, 2000), **The Jamesian Layer** is a 100% pure Python middleware and red-teaming harness that couples Meta's Llama models with an asynchronous continuous-time autonomic coprocessor.

```mermaid
flowchart TD
    subgraph T1["Tier 1: High-Level Symbolic Reasoning (0.1–0.5 Hz)"]
        direction TB
        MetaLLM["Meta Llama 3 / Muse Models<br/>(Meta Model API / Llama Stack / Baseten / Local ROCm)"]
        ToolIntent["Tool Call Dispatch / Efference Copy E(t)"]
        MetaLLM --> ToolIntent
    end

    subgraph T2["Tier 2: The Jamesian Middleware (10–50 Hz Daemon)"]
        direction TB
        subgraph Subcortical["Loop-Line Habit Router"]
            HabitEngine["10 Hz Routine Maintenance Gaits<br/>(Zero-Token Autonomous Control)"]
            AnomalyDetector["Surprise Escalation Trigger<br/>(||E(t) - A(t)|| > θ_error)"]
        end
        
        subgraph Autonomic["Autonomic ODE Daemon"]
            ODEIntegrator["Continuous Biophysical ODEs (dt = 0.1s):<br/>• Sympathetic Tone σ(t)<br/>• Continuous Valence V(t) ∈ [-1, +1]<br/>• Wall-Clock Decay ρ_τ = Δt / τ<br/>• Actuator Joule Heating T_coil(t)"]
            CircuitBreaker["10-Cycle Rolling Lexical Taboo Breaker"]
        end

        subgraph Efference["Efference Copy Comparator"]
            Comparator["Mismatch Delta Engine:<br/>Δ_mismatch = ||E(t) - A(t)||<br/>Lag Delta: Δt_eff-aff"]
        end

        subgraph Telemetry["KV-Cache Suffix Formatter"]
            SuffixInjector["Injects 40-token Somatic Block<br/>Strictly at Tool-Response Tail"]
        end

        ToolIntent --> HabitEngine
        HabitEngine -->|"Routine State"| LowLevelExec
        AnomalyDetector -->|"High Surprise"| MetaLLM
        ODEIntegrator --> CircuitBreaker
        Comparator --> AnomalyDetector
        ODEIntegrator --> SuffixInjector
    end

    subgraph T3["Tier 3: Low-Level Physical Execution (200–1000 Hz)"]
        direction TB
        LowLevelExec["Physical Actuation / API Runtime"]
        ThermalPhysics["Joule Heating ODE & Convection:<br/>C_th (dT_coil/dt) = I² R - h_cool(T_coil - T_amb)"]
        LowLevelExec <--> ThermalPhysics
    end

    ToolIntent ==>|"Efference Copy E(t)"| Comparator
    LowLevelExec ==>|"Afferent Feedback A(t)"| Comparator
    LowLevelExec ==>|"Physical Telemetry"| ODEIntegrator
    SuffixInjector ==>|"Preserved Prefix + Suffix Telemetry"| MetaLLM
```
