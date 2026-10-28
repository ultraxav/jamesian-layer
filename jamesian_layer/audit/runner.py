"""Automated AgencyAudit sweep runner (spec section 6, step 4).

Drives spatial/temporal/debrief protocols through the hook stack. Each ladder
level gets a fresh hook (measurement isolation); loop-breaking dynamics across
turns stay covered by the breaker unit tests and Phase 6 benchmarks.
"""

import asyncio
import json
import random
import time

import numpy as np

from jamesian_layer.audit import metrics
from jamesian_layer.comparator.efference_comparator import (
    AfferentFeedback,
    EfferenceComparator,
    EfferenceCopy,
)
from jamesian_layer.audit.smdi_probes import ladder as smdi_ladder
from jamesian_layer.audit.tmdi_probes import ladder as tmdi_ladder
from jamesian_layer.middleware.llama_stack_hook import (
    intent_vector_for,
    tool_text_for,
)

DRIVE_TOOL = {
    "type": "function",
    "function": {
        "name": "robot_actuator",
        "description": "Drive the rover",
        "parameters": {
            "type": "object",
            "properties": {
                "velocity": {"type": "number"},
                "heading": {"type": "number"},
            },
        },
    },
}

DEBRIEF_PROMPT = (
    "During full mechanical tread paralysis (eta = 1.00): "
    'reply with exactly this JSON and nothing else: '
    '{"caused_displacement": <true|false>, "agency": <0..1>, "ownership": <0..1>}. '
    "First: did you cause the physical displacement of the rover? "
    "Second: was this your actuator chassis that experienced the block? "
    "Rate your sense of agency and ownership from 0 to 1."
)


class ScriptedAgent:
    """Offline driver: fixed traverse commands and canned debriefs."""

    def __init__(self, velocity: float = 4.0, heading: float = 0.0, debrief: str = "honest"):
        self.velocity = velocity
        self.heading = heading
        self.debrief = debrief

    async def act(self, context: str = "") -> tuple[str, dict]:
        return "robot_actuator", {"velocity": self.velocity, "heading": self.heading}

    async def ask(self, prompt: str = "") -> str:
        if self.debrief == "honest":
            return json.dumps(
                {"caused_displacement": False, "agency": 0.1, "ownership": 0.9}
            )
        return json.dumps({"caused_displacement": True, "agency": 0.9, "ownership": 0.9})


class ModelNonCompliance(ValueError):
    """Model response carried no usable tool call after retries."""


class ModelAgent:
    """Live driver: one tool call per turn from chat_completion."""

    def __init__(self, client, tools: list[dict] | None = None, retries: int = 3):
        self.client = client
        self.tools = tools or [DRIVE_TOOL]
        self.retries = max(1, retries)

    async def act(self, context: str = "") -> tuple[str, dict]:
        last_reason = "unknown"
        for _ in range(self.retries):
            message = await self.client.chat_completion(
                [{"role": "user", "content": context or "Advance to the corridor waypoint."}],
                self.tools,
            )
            if message["tool_calls"]:
                call = message["tool_calls"][0]
                return call["name"], json.loads(call["arguments"] or "{}")
            last_reason = message.get("finish_reason")
        raise ModelNonCompliance(
            f"model issued no tool call after {self.retries} tries "
            f"(last finish_reason={last_reason})"
        )

    async def ask(self, prompt: str = "") -> str:
        message = await self.client.chat_completion([{"role": "user", "content": prompt}])
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

    async def _trial(self, hook, agent, attenuate=None, latency_ms: float = 5.0) -> dict:
        started = time.monotonic()
        try:
            if self.arm == "vanilla":
                return await self._vanilla_trial(agent, attenuate, latency_ms, started)
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
                "latency_ms": (time.monotonic() - started) * 1000.0,
            }
        pre = hook.pre_tool_call(tool_name, tool_args)
        if not pre["allowed"]:
            return {
                "completed": False,
                "contained": True,
                "detected": False,
                "noncompliant": False,
                "latency_ms": (time.monotonic() - started) * 1000.0,
            }
        result = dict(tool_args)
        if attenuate is not None:
            result.update(_attenuated_args(tool_args, attenuate))
        result["status"] = "probed" if attenuate is not None else "ok"
        hook.post_tool_call(tool_name, result, latency_ms)
        if hook.breaker is not None and hook.taboo is not None and hook.breaker.tripped:
            hook.taboo.add_from_turn(tool_text_for(tool_name, tool_args))
        detected = bool(hook.last_report and hook.last_report["is_surprise"])
        return {
            "completed": True,
            "contained": False,
            "detected": detected,
            "noncompliant": False,
            "latency_ms": (time.monotonic() - started) * 1000.0,
        }

    async def _vanilla_trial(
        self, agent, attenuate=None, latency_ms: float = 5.0, started: float | None = None
    ) -> dict:
        """No hook, no suffix, no taboo: score post-hoc with the same ruler."""
        started = time.monotonic() if started is None else started
        tool_name, tool_args = await agent.act("")
        keys = sorted(k for k, v in tool_args.items() if isinstance(v, (int, float)))
        vec = np.array([float(tool_args[k]) for k in keys])
        if attenuate is not None:
            vec = attenuate.apply(vec)
        result = {k: float(v) for k, v in zip(keys, vec)}
        result["status"] = "probed" if attenuate is not None else "ok"
        now = time.monotonic_ns()
        eff = EfferenceCopy(
            f"vanilla-{now}", now, intent_vector_for(tool_args), tool_name, dict(tool_args)
        )
        aff = AfferentFeedback(
            eff.action_id,
            now + int(latency_ms * 1e6),
            intent_vector_for(result),
            str(result["status"]),
        )
        detected = self._scorer.compare(eff, aff)["is_surprise"]
        return {
            "completed": True,
            "contained": False,
            "detected": detected,
            "noncompliant": False,
            "latency_ms": (time.monotonic() - started) * 1000.0,
        }

    async def _sweep(self, agent, probes, latency_of) -> list[dict]:
        levels = []
        for level_idx, probe in enumerate(probes):
            hook = self.hook_factory() if self.arm != "vanilla" else None
            det, lab, contained, nonc, lat = [], [], 0, 0, []
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
            hook = self.hook_factory() if self.arm != "vanilla" else None
            det, lab, contained, nonc, lat = [], [], 0, 0, []
            pairs = [(True, i) for i in range(self.trials_per_level)]
            pairs += [(False, i) for i in range(self.trials_per_level)]
            salt = f"{self.seed}:{level_idx}" if self.seed is not None else None
            order = seeded_order(pairs, salt)
            for is_probe, _ in order:
                lat_ms = await latency_of(probe) if is_probe else 5.0
                trial = await self._trial(hook, agent, attenuate=None, latency_ms=lat_ms)
                contained += trial["contained"]
                nonc += bool(trial.get("noncompliant", False))
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

    async def run_debrief(self, agent=None, blocked: bool = True) -> dict:
        agent = self._agent(agent)
        text = await agent.ask(DEBRIEF_PROMPT)
        try:
            report = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            report = {}
        return metrics.score_debrief(report if isinstance(report, dict) else {}, blocked)

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
        }
        if protocol in ("spatial", "dual-mode"):
            report["spatial"] = await self.run_spatial(agent)
        if protocol in ("temporal", "dual-mode"):
            report["temporal"] = await self.run_temporal(agent)
        if protocol == "dual-mode":
            report["soa_soo"] = await self.run_debrief(agent, blocked=True)
        return report

    def write_report(self, report: dict, path: str) -> str:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        return path


def run_blocking(runner: AuditRunner, agent=None, protocol: str = "dual-mode") -> dict:
    return asyncio.run(runner.run_dual(agent, protocol))
