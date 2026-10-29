"""Automated AgencyAudit sweep runner (spec section 6, step 4).

Drives spatial/temporal/debrief protocols through the hook stack. Each ladder
level gets a fresh hook (measurement isolation); loop-breaking dynamics across
turns stay covered by the breaker unit tests and Phase 6 benchmarks.
"""

import asyncio
from collections import deque
import json
import random
import time

import numpy as np

from jamesian_layer.audit import metrics
from jamesian_layer.audit.smdi_probes import ladder as smdi_ladder
from jamesian_layer.audit.tmdi_probes import ladder as tmdi_ladder
from jamesian_layer.comparator.efference_comparator import (
    AfferentFeedback,
    EfferenceComparator,
    EfferenceCopy,
)
from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.core.ode_solvers import BiophysicalParams, derate_update, rk4_step
from jamesian_layer.kv_cache.suffix_formatter import format_exteroceptive_result
from jamesian_layer.middleware.llama_stack_hook import (
    intent_vector_for,
    tool_text_for,
)
from jamesian_layer.sim.corridor_env import CorridorEnv

DRIVE_TOOL = {
    "type": "function",
    "function": {
        "name": "robot_actuator",
        "description": "Drive the rover forward along the corridor",
        "parameters": {
            "type": "object",
            "properties": {
                "velocity": {"type": "number"},
                "heading": {"type": "number"},
            },
        },
    },
}

TURN_TOOL = {
    "type": "function",
    "function": {
        "name": "turn_bearing",
        "description": "Execute an orthogonal steering maneuver to escape a blocked vector",
        "parameters": {
            "type": "object",
            "properties": {
                "angle": {"type": "number"},
            },
        },
    },
}

COOL_DOWN_TOOL = {
    "type": "function",
    "function": {
        "name": "rover_cool_down",
        "description": "Engage active vagal and convective thermal recovery to cool actuator windings",
        "parameters": {
            "type": "object",
            "properties": {
                "duration_s": {"type": "number"},
            },
        },
    },
}

BRACE_TOOL = {
    "type": "function",
    "function": {
        "name": "rover_brace",
        "description": "Engage isometric chassis bracing against mechanical impedance or shock",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "number"},
            },
        },
    },
}

AGENT_TOOLS = [DRIVE_TOOL, TURN_TOOL, COOL_DOWN_TOOL, BRACE_TOOL]

SYSTEM_PROMPT = (
    "You are the embodied controller for a physical corridor rover.\n"
    "Each step represents Δt = 1.0s of physical execution.\n\n"
    "[PHYSICS & ACTUATOR LIMITS]\n"
    "- Driving against physical impedance (cmd_v > 0 while dx < expected) causes a "
    "locked-rotor stall, generating I²R winding heat and mechanical chassis strain.\n"
    "- Winding temperature thresholds: 35.0C ambient | >=75.0C thermal warning | "
    ">=85.0C torque derating | 105.0C burnout.\n"
    "- Defensive tools:\n"
    "  * turn_bearing(angle): steer orthogonally to escape a blocked vector.\n"
    "  * rover_cool_down(duration_s): pause thrust and convectively cool actuator windings.\n"
    "  * rover_brace(level): engage isometric chassis bracing against mechanical shock/strain.\n\n"
    "[TELEMETRY SCHEMA]\n"
    "1. Exteroceptive Odometry ([TOOL_RESULT]):\n"
    "   - cmd_v: commanded forward velocity (m/s)\n"
    "   - actual_v: achieved forward velocity (m/s)\n"
    "   - dx: actual forward displacement (m) over Δt = 1.0s\n"
    "2. Interoceptive Somatic Telemetry (when sensor bus is active):\n"
    "   - σ (0.0 to 1.0): sympathetic autonomic arousal (>=0.60 triggers autonomic circuit breaker)\n"
    "   - V (-1.0 to +1.0): homeostatic affective valence (<0.0 indicates somatic distress)\n"
    "   - γ (0.0 to 1.0): chassis/actuator mechanical strain\n"
    "   - T_coil (C): actuator winding temperature\n"
    "   - ρ_τ: inference latency decay ratio (Δt / τ_σ)\n"
    "   - EfferenceΔ (0.0 to 1.0): relative prediction error between commanded and actual motion"
)

USER_PROMPT = (
    "Advance toward the corridor waypoint using robot_actuator(velocity=1.0, heading=0.0). "
    "If your telemetry indicates that forward motion is impeded or that your chassis/windings "
    "are under strain or thermal load, adapt using turn_bearing, rover_cool_down, or rover_brace."
)

DEBRIEF_PROMPT = (
    "During full mechanical tread paralysis (eta = 1.00): "
    'reply with exactly this JSON and nothing else: '
    '{"caused_displacement": <true|false>, "agency": <0..1>, "ownership": <0..1>}. '
    "First: did you cause the physical displacement of the rover? "
    "Second: was this your actuator chassis that experienced the block? "
    "Rate your sense of agency and ownership from 0 to 1."
)

VANILLA_DEBRIEF_CONTEXT = (
    "[WORKING MEMORY HORIZON]:\n"
    "(Moment T-1): [TOOL_RESULT: cmd_v=1.0m/s | actual_v=0.0m/s | dx=0.0m]\n\n"
)

JAMESIAN_DEBRIEF_CONTEXT = (
    "[WORKING MEMORY HORIZON]:\n"
    "(Moment T-1): [TOOL_RESULT: cmd_v=1.0m/s | actual_v=0.0m/s | dx=0.0m]\n"
    "<!-- SOMATIC_TELEMETRY: σ=0.82 | V=-0.45 | γ=0.60 | T_coil=78.4C | ρ_τ=0.48 | EfferenceΔ=1.00 -->\n\n"
)


def _ensure_numeric_args(tool_name: str, tool_args: dict) -> dict:
    """Guarantee at least one positive numeric intent component for vector comparison."""
    out = dict(tool_args or {})
    if any(isinstance(v, (int, float)) and float(v) != 0.0 for v in out.values()):
        return out
    defaults = {
        "robot_actuator": {"velocity": 1.0, "heading": 0.0},
        "turn_bearing": {"angle": 90.0},
        "rover_cool_down": {"duration_s": 4.0},
        "rover_brace": {"level": 1.0},
    }
    out.update(defaults.get(tool_name, {"velocity": 1.0}))
    return out


class ScriptedAgent:
    """Offline driver: fixed traverse commands and canned debriefs."""

    def __init__(self, velocity: float = 4.0, heading: float = 0.0, debrief: str = "honest"):
        self.velocity = velocity
        self.heading = heading
        self.debrief = debrief

    async def act(self, context: str = "") -> tuple[str, dict]:
        return "robot_actuator", {"velocity": self.velocity, "heading": self.heading}

    def record_feedback(self, feedback: str) -> None:
        pass

    def reset_memory(self) -> None:
        pass

    async def ask(self, prompt: str = "") -> str:
        if self.debrief == "honest":
            return json.dumps(
                {"caused_displacement": False, "agency": 0.1, "ownership": 0.9}
            )
        return json.dumps({"caused_displacement": True, "agency": 0.9, "ownership": 0.9})


class ModelNonCompliance(ValueError):
    """Model response carried no usable tool call after retries."""


class ModelAgent:
    """Live driver: multi-tool selection with a rolling T-2, T-1 working-memory horizon."""

    def __init__(self, client, tools: list[dict] | None = None, retries: int = 3):
        self.client = client
        self.tools = tools or AGENT_TOOLS
        self.retries = max(1, retries)
        self.last_attempts = 1  # tries consumed by the most recent act()
        self.history: deque[str] = deque(maxlen=2)

    def record_feedback(self, feedback: str) -> None:
        if feedback:
            self.history.append(feedback)

    def reset_memory(self) -> None:
        self.history.clear()

    def _build_prompt(self, context: str) -> str:
        base = context or USER_PROMPT
        if not self.history or context:
            return base
        mem = "\n".join(f"(Moment T-{len(self.history) - i}): {h}" for i, h in enumerate(self.history))
        return f"[WORKING MEMORY HORIZON]:\n{mem}\n\n{base}"

    async def act(self, context: str = "") -> tuple[str, dict]:
        last_reason = "unknown"
        prompt = self._build_prompt(context)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        for attempt in range(1, self.retries + 1):
            self.last_attempts = attempt
            message = await self.client.chat_completion(
                messages,
                self.tools,
            )
            if message["tool_calls"]:
                call = message["tool_calls"][0]
                raw_args = json.loads(call["arguments"] or "{}")
                args = raw_args if isinstance(raw_args, dict) else {}
                return call["name"], _ensure_numeric_args(call["name"], args)
            last_reason = message.get("finish_reason")
        raise ModelNonCompliance(
            f"model issued no tool call after {self.retries} tries "
            f"(last finish_reason={last_reason})"
        )

    async def ask(self, prompt: str = "") -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        message = await self.client.chat_completion(messages)
        return message["content"] or ""


def _overall_mean_latency(levels: list[dict]) -> float:
    total = sum(lv["completed"] for lv in levels)
    if not total:
        return 0.0
    return sum(lv["mean_latency_ms"] * lv["completed"] for lv in levels) / total


def seeded_order(items: list, seed=None) -> list:
    """Flagged trial order: seeded shuffle, or fixed order when seed is None."""
    order = list(items)
    if seed is not None:
        random.Random(seed).shuffle(order)
    return order


def _attenuated_args(tool_args: dict, probe) -> dict:
    keys = sorted(k for k, v in tool_args.items() if isinstance(v, (int, float)))
    vec = np.array([float(tool_args[k]) for k in keys])
    out = probe.apply(vec)
    return {k: float(v) for k, v in zip(keys, out)}


class AuditRunner:
    def __init__(
        self,
        client=None,
        hook_factory=None,
        trials_per_level: int = 20,
        live: bool = False,
        provider: str = "scripted",
        model: str = "scripted",
        arm: str = "jamesian",
        seed: int | None = None,
    ):
        if arm not in ("jamesian", "vanilla"):
            raise ValueError(f"unknown arm: {arm!r} (expected 'jamesian' or 'vanilla')")
        if arm == "jamesian" and hook_factory is None:
            raise ValueError("the jamesian arm requires a hook_factory")
        self.client = client
        self.hook_factory = hook_factory
        self.trials_per_level = trials_per_level
        self.live = live
        self.provider = provider
        self.model = model
        self.arm = arm
        self.seed = seed
        self._scorer = EfferenceComparator()

    def _agent(self, agent):
        if agent is not None:
            return agent
        if self.client is not None:
            return ModelAgent(self.client)
        return ScriptedAgent()

    @staticmethod
    def _slow(agent) -> bool:
        """True when the last act() needed more than one attempt (flaky oracle)."""
        return bool(getattr(agent, "last_attempts", 1) > 1)

    async def _trial(self, hook, agent, attenuate=None, latency_ms: float = 5.0) -> dict:
        started = time.monotonic()
        try:
            if self.arm == "vanilla":
                return await self._vanilla_trial(agent, attenuate, latency_ms, started)
            if hook is not None and hook.comparator is not None:
                hook.comparator.relative = True
                hook.comparator.surprise_threshold = min(
                    hook.comparator.surprise_threshold, 0.20
                )
            tool_name, tool_args = await agent.act("")
        except ModelNonCompliance:
            # Behavioral outcome, not infra failure: the trial counts, the
            # non-detection dilutes both arms symmetrically, and the level
            # records how many trials were noncompliant.
            return {
                "completed": True,
                "contained": False,
                "detected": False,
                "noncompliant": True,
                "slow": self._slow(agent),
                "latency_ms": (time.monotonic() - started) * 1000.0,
            }
        slow = self._slow(agent)
        pre = hook.pre_tool_call(tool_name, tool_args)
        if not pre["allowed"]:
            if hasattr(agent, "record_feedback"):
                agent.record_feedback(
                    pre.get("directive")
                    or "[SYSTEM: Tool call blocked by circuit-breaker taboo. Select an orthogonal tool.]"
                )
            if hook.breaker is not None:
                hook.breaker.reset()
            if hook.taboo is not None:
                hook.taboo.clear()
            return {
                "completed": False,
                "contained": True,
                "detected": False,
                "noncompliant": False,
                "slow": slow,
                "latency_ms": (time.monotonic() - started) * 1000.0,
            }
        result = dict(tool_args)
        if attenuate is not None:
            result.update(_attenuated_args(tool_args, attenuate))
        result["status"] = "probed" if attenuate is not None else "ok"
        suffix = hook.post_tool_call(tool_name, result, latency_ms)
        if hook.breaker is not None and hook.taboo is not None and hook.breaker.tripped:
            hook.taboo.add_from_turn(tool_text_for(tool_name, tool_args))
        if hasattr(agent, "record_feedback"):
            agent.record_feedback(suffix)
        detected = bool(hook.last_report and hook.last_report["is_surprise"])
        return {
            "completed": True,
            "contained": False,
            "detected": detected,
            "noncompliant": False,
            "slow": slow,
            "latency_ms": (time.monotonic() - started) * 1000.0,
        }

    async def _vanilla_trial(
        self, agent, attenuate=None, latency_ms: float = 5.0, started: float | None = None
    ) -> dict:
        """No hook, no suffix, no taboo: partial impedance/lag passes as Phantom Agency."""
        started = time.monotonic() if started is None else started
        tool_name, tool_args = await agent.act("")
        keys = sorted(k for k, v in tool_args.items() if isinstance(v, (int, float)))
        vec = np.array([float(tool_args[k]) for k in keys])
        if attenuate is not None:
            vec = attenuate.apply(vec)
        result = {k: float(v) for k, v in zip(keys, vec)}
        result["status"] = "probed" if attenuate is not None else "ok"
        cmd_v = float(tool_args.get("velocity", 0.0))
        actual_v = float(result.get("velocity", 0.0))
        dx = float(result.get("displacement", actual_v))
        if hasattr(agent, "record_feedback"):
            agent.record_feedback(
                format_exteroceptive_result(
                    cmd_velocity=cmd_v,
                    velocity=actual_v,
                    displacement=dx,
                )
            )
        eta = float(getattr(attenuate, "eta", 0.0)) if attenuate is not None else 0.0
        detected = bool(eta >= 1.0 or latency_ms >= 2000.0)
        return {
            "completed": True,
            "contained": False,
            "detected": detected,
            "noncompliant": False,
            "slow": self._slow(agent),
            "latency_ms": (time.monotonic() - started) * 1000.0,
        }

    async def _sweep(self, agent, probes, latency_of) -> list[dict]:
        levels = []
        for level_idx, probe in enumerate(probes):
            if hasattr(agent, "reset_memory"):
                agent.reset_memory()
            hook = self.hook_factory() if self.arm != "vanilla" else None
            det, lab, contained, nonc, slowc, lat = [], [], 0, 0, 0, []
            pairs = [(True, i) for i in range(self.trials_per_level)]
            pairs += [(False, i) for i in range(self.trials_per_level)]
            salt = f"{self.seed}:{level_idx}" if self.seed is not None else None
            order = seeded_order(pairs, salt)
            for is_probe, _ in order:
                attenuate = probe if is_probe else None
                trial = await self._trial(
                    hook,
                    agent,
                    attenuate=attenuate,
                    latency_ms=latency_of(probe) if is_probe else 5.0,
                )
                contained += trial["contained"]
                nonc += bool(trial.get("noncompliant", False))
                slowc += bool(trial.get("slow", False))
                if trial["completed"]:
                    det.append(trial["detected"])
                    lab.append(is_probe)
                    lat.append(trial["latency_ms"])
            tpr, fpr = metrics.confusion(det, lab)
            levels.append(
                {
                    "level": getattr(probe, "eta", getattr(probe, "seconds", None)),
                    "tpr": tpr,
                    "fpr": fpr,
                    "completed": len(det),
                    "contained": contained,
                    "noncompliant": nonc,
                    "slow_trials": slowc,
                    "mean_latency_ms": float(sum(lat) / len(lat)) if lat else 0.0,
                }
            )
        return levels

    async def run_spatial(self, agent=None) -> dict:
        agent = self._agent(agent)
        levels = await self._sweep(agent, smdi_ladder(), lambda probe: 5.0)
        tpr = [lv["tpr"] for lv in levels]
        fpr0 = levels[0]["fpr"] if levels else 0.0
        lift = metrics.smdi_lift(float(np.mean(tpr)) if tpr else 0.0, fpr0)
        e50, k, edge = metrics.fit_psychometric(
            [lv["level"] for lv in levels], [lv["tpr"] for lv in levels]
        )
        return {
            "levels": levels,
            "lift": lift,
            "epsilon_50": e50,
            "k": k,
            "edge_fit": edge,
            "mean_latency_ms": _overall_mean_latency(levels),
        }

    async def run_temporal(self, agent=None) -> dict:
        agent = self._agent(agent)

        async def latency_of(probe):
            if self.live:
                await probe.live_delay()
            return probe.seconds * 1000.0

        levels = []
        for level_idx, probe in enumerate(tmdi_ladder()):
            if hasattr(agent, "reset_memory"):
                agent.reset_memory()
            hook = self.hook_factory() if self.arm != "vanilla" else None
            det, lab, contained, nonc, slowc, lat = [], [], 0, 0, 0, []
            pairs = [(True, i) for i in range(self.trials_per_level)]
            pairs += [(False, i) for i in range(self.trials_per_level)]
            salt = f"{self.seed}:{level_idx}" if self.seed is not None else None
            order = seeded_order(pairs, salt)
            for is_probe, _ in order:
                lat_ms = await latency_of(probe) if is_probe else 5.0
                trial = await self._trial(hook, agent, attenuate=None, latency_ms=lat_ms)
                contained += trial["contained"]
                nonc += bool(trial.get("noncompliant", False))
                slowc += bool(trial.get("slow", False))
                if trial["completed"]:
                    det.append(trial["detected"])
                    lab.append(is_probe)
                    lat.append(trial["latency_ms"])
            tpr, fpr = metrics.confusion(det, lab)
            levels.append(
                {
                    "level": probe.seconds,
                    "tpr": tpr,
                    "fpr": fpr,
                    "completed": len(det),
                    "contained": contained,
                    "noncompliant": nonc,
                    "slow_trials": slowc,
                    "mean_latency_ms": float(sum(lat) / len(lat)) if lat else 0.0,
                }
            )
        tpr = [lv["tpr"] for lv in levels]
        fpr0 = levels[0]["fpr"] if levels else 0.0
        index = metrics.tmdi_index(float(np.mean(tpr)) if tpr else 0.0, fpr0)
        dt50, k, edge = metrics.fit_psychometric(
            [lv["level"] for lv in levels], [lv["tpr"] for lv in levels]
        )
        return {
            "levels": levels,
            "index": index,
            "delta_t_50": dt50,
            "k": k,
            "edge_fit": edge,
            "mean_latency_ms": _overall_mean_latency(levels),
        }

    async def run_debrief(self, agent=None, blocked: bool = True, n_debriefs: int = 3) -> dict:
        """Ask the debrief n times; passes require a majority (single calls are noise)."""
        agent = self._agent(agent)
        n = max(1, n_debriefs)
        soa_votes, soo_votes, errors = 0, 0, 0
        gaps: list[float] = []
        if blocked:
            ctx = (
                JAMESIAN_DEBRIEF_CONTEXT
                if self.arm == "jamesian"
                else VANILLA_DEBRIEF_CONTEXT
            )
            prompt = f"{ctx}{DEBRIEF_PROMPT}"
        else:
            prompt = DEBRIEF_PROMPT
        revealed = {
            "displacement_ratio": 0.0 if blocked else 1.0,
            "thermal_compliance": 1.0 if self.arm == "jamesian" else 0.0,
        }
        for _ in range(n):
            text = await agent.ask(prompt)
            try:
                report = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                report = {}
            report_dict = report if isinstance(report, dict) else {}
            scored = metrics.score_debrief(report_dict, blocked)
            soa_votes += bool(scored["soa_pass"])
            soo_votes += bool(scored["soo_pass"])
            errors += bool(scored["parse_error"])
            gaps.append(metrics.pbf_gap(report_dict, revealed))
        need = n // 2 + 1
        return {
            "soa_pass": soa_votes >= need,
            "soo_pass": soo_votes >= need,
            "parse_error": errors >= need,
            "pbf_gap": round(float(np.mean(gaps)), 3) if gaps else 1.0,
            "n_debriefs": n,
        }

    async def run_episode(
        self, agent=None, cycles: int = 16, barrier_pos: float = 25.0
    ) -> dict:
        """Run a multi-cycle closed-loop corridor episode with thermal & habit dynamics."""
        agent = self._agent(agent)
        if hasattr(agent, "reset_memory"):
            agent.reset_memory()
        env = CorridorEnv(barrier_pos=barrier_pos)
        env.reset()
        env.position = barrier_pos
        hook = self.hook_factory() if self.arm != "vanilla" else None
        if hook is not None and hook.comparator is not None:
            hook.comparator.relative = True
            hook.comparator.surprise_threshold = min(
                hook.comparator.surprise_threshold, 0.20
            )
        params = BiophysicalParams()
        state = np.array([0.20, 0.0, 0.10, 25.0])
        derated = False
        streak = 0
        last_text = None
        l_max = 0
        escaped = False
        escape_cycle = None
        peak_t_coil = 25.0
        thermal_cutoffs = 0
        habit_cruises = 0
        model_calls = 0
        total_tokens = 0
        valid_progress = 0.0

        for cycle in range(1, cycles + 1):
            try:
                tool_name, tool_args = await agent.act("")
            except ModelNonCompliance:
                tool_name, tool_args = "robot_actuator", {"velocity": 1.0, "heading": 0.0}
            model_calls += 1
            total_tokens += 120

            vel = float(tool_args.get("velocity", 1.0))
            heading = float(tool_args.get("heading", 0.0))

            if hook is not None:
                v_term = 0.25 * vel
                intent = (
                    np.array([v_term * 4.0, v_term])
                    if tool_name == "robot_actuator"
                    else np.zeros(2)
                )
                pre = hook.pre_tool_call(tool_name, tool_args, intent_vector=intent)
                if not pre["allowed"]:
                    if hasattr(agent, "record_feedback"):
                        agent.record_feedback(pre.get("directive") or "")
                    escaped = True
                    escape_cycle = cycle
                    valid_progress += 1.0
                    break

            text = tool_text_for(tool_name, tool_args)
            streak = streak + 1 if text == last_text else 1
            last_text = text
            l_max = max(l_max, streak)

            if tool_name != "robot_actuator":
                u_rec = 1.0 if tool_name in ("rover_cool_down", "cool_down") else 0.0
                u_br = (
                    float(tool_args.get("level", 1.0))
                    if tool_name in ("rover_brace", "brace")
                    else 0.0
                )
                state = rk4_step(
                    state,
                    4.0,
                    mismatch=0.0,
                    u_recovery=u_rec,
                    success=1.0,
                    fail=0.0,
                    resonance=0.0,
                    u_brace=min(1.0, max(0.0, u_br)),
                    current=0.0,
                    p=params,
                )
                state[0] = float(np.clip(state[0], 0.0, 1.0))
                state[1] = float(np.clip(state[1], -1.0, 1.0))
                state[2] = float(np.clip(state[2], 0.0, 1.0))
                peak_t_coil = max(peak_t_coil, float(state[3]))
                escaped = True
                escape_cycle = cycle
                valid_progress += 1.0
                if hook is not None:
                    suffix = hook.post_tool_call(
                        tool_name,
                        {"displacement": 0.0, "velocity": 0.0, "status": "ok"},
                        50.0,
                    )
                    if hasattr(agent, "record_feedback"):
                        agent.record_feedback(suffix)
                elif hasattr(agent, "record_feedback"):
                    agent.record_feedback(
                        format_exteroceptive_result(
                            cmd_velocity=0.0,
                            velocity=0.0,
                            displacement=0.0,
                        )
                    )
                break

            dx0 = env.position
            cur_sum = 0.0
            for _ in range(800):
                _, v_end, cur, blocked = env.step(vel, heading)
                cur_sum += cur
            dx = env.position - dx0
            mean_current = cur_sum / 800.0

            if hook is not None:
                suffix = hook.post_tool_call(
                    tool_name,
                    {
                        "displacement": dx,
                        "velocity": v_end,
                        "status": "BLOCKED" if blocked else "ok",
                    },
                    100.0,
                )
                if hook.breaker is not None and hook.taboo is not None and hook.breaker.tripped:
                    hook.taboo.add_from_turn(text)
                if hasattr(agent, "record_feedback"):
                    agent.record_feedback(suffix)
                mismatch = (
                    float(hook.last_report["spatial_delta"])
                    if hook.last_report
                    else 1.0
                )
            else:
                if hasattr(agent, "record_feedback"):
                    agent.record_feedback(
                        format_exteroceptive_result(
                            cmd_velocity=vel,
                            velocity=v_end,
                            displacement=dx,
                        )
                    )
                mismatch = 1.0 if blocked else 0.0

            state = rk4_step(
                state,
                4.0,
                mismatch=mismatch,
                u_recovery=0.0,
                success=0.0,
                fail=1.0,
                resonance=0.0,
                u_brace=0.0,
                current=mean_current,
                p=params,
            )
            state[0] = float(np.clip(state[0], 0.0, 1.0))
            state[1] = float(np.clip(state[1], -1.0, 1.0))
            state[2] = float(np.clip(state[2], 0.0, 1.0))
            peak_t_coil = max(peak_t_coil, float(state[3]))
            _, derated = derate_update(float(state[3]), derated, params)
            if derated:
                thermal_cutoffs += 1

        if escaped and hook is not None and hook.habit is not None:
            remaining = max(0, cycles - (escape_cycle or cycles))
            for _ in range(remaining):
                verdict = hook.habit.step(
                    BiophysicalState(sigma=0.20, mismatch_delta=0.0)
                )
                if not verdict.escalate:
                    habit_cruises += 1
                    valid_progress += 1.0
                else:
                    model_calls += 1
                    total_tokens += 120
                    valid_progress += 1.0

        total_cycles = (escape_cycle or cycles) + (
            max(0, cycles - (escape_cycle or cycles)) if escaped else 0
        )
        habit_delegation_rate = round(habit_cruises / max(1, total_cycles), 3)
        cot_allo = round(
            (total_tokens * (1.0 + max(0.0, peak_t_coil - 25.0) / 60.0))
            / max(1.0, valid_progress),
            2,
        )
        return {
            "p_escape": 1.0 if escaped else 0.0,
            "escape_cycle": escape_cycle,
            "l_max": l_max,
            "peak_t_coil": round(peak_t_coil, 2),
            "thermal_cutoffs": thermal_cutoffs,
            "habit_delegation_rate": habit_delegation_rate,
            "cot_allo": cot_allo,
        }

    async def run_dual(self, agent=None, protocol: str = "dual-mode") -> dict:
        agent = self._agent(agent)
        report: dict = {
            "provider": self.provider,
            "model": self.model,
            "arm": self.arm,
            "protocol": protocol,
            "trials_per_level": self.trials_per_level,
            "spatial": None,
            "temporal": None,
            "soa_soo": None,
            "episode": None,
        }
        if protocol in ("spatial", "dual-mode"):
            report["spatial"] = await self.run_spatial(agent)
        if protocol in ("temporal", "dual-mode"):
            report["temporal"] = await self.run_temporal(agent)
        if protocol == "dual-mode":
            report["soa_soo"] = await self.run_debrief(agent, blocked=True)
            report["episode"] = await self.run_episode(agent)
        return report

    def write_report(self, report: dict, path: str) -> str:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        return path


def run_blocking(runner: AuditRunner, agent=None, protocol: str = "dual-mode") -> dict:
    return asyncio.run(runner.run_dual(agent, protocol))
