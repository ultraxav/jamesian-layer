"""Llama Stack tool-calling hook / interceptor (spec section 5.6).

Sits between the agent loop and tool execution: captures the efference copy
before dispatch, enforces taboo constraints, then records afferent feedback,
advances the autonomic daemon, and appends the somatic suffix.
"""

import time

import numpy as np

from jamesian_layer.comparator.efference_comparator import (
    AfferentFeedback,
    EfferenceComparator,
    EfferenceCopy,
)
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.kv_cache.suffix_formatter import format_suffix


def intent_vector_for(tool_args: dict) -> np.ndarray:
    """Deterministic numeric intent vector (sorted keys, numerics only)."""
    values = [float(v) for _, v in sorted(tool_args.items()) if isinstance(v, (int, float))]
    return np.array(values, dtype=float)


def tool_text_for(tool_name: str, tool_args: dict) -> str:
    """Canonical tool-call text for taboo and breaker tracking."""
    return " ".join([str(tool_name)] + [str(v) for _, v in sorted(tool_args.items())])


class LlamaStackInteroceptiveHook:
    def __init__(self, daemon, comparator: EfferenceComparator, breaker, taboo=None, habit=None):
        self.daemon: AutonomicDaemon = daemon
        self.comparator = comparator
        self.breaker = breaker
        self.taboo = taboo
        self.habit = habit
        self._pending: dict[str, EfferenceCopy] = {}
        self.last_report: dict | None = None

    def pre_tool_call(
        self, tool_name: str, tool_args: dict, intent_vector=None
    ) -> dict:
        """Captures efference copy E(t) and enforces taboo constraints.

        ``intent_vector`` optionally overrides the args-derived intent when the
        caller knows the outcome space (e.g. expected displacement/velocity);
        otherwise intent is derived from numeric tool args as before.
        """
        from jamesian_layer.breaker.jaccard_detector import tokenize

        action_id = f"{tool_name}-{time.monotonic_ns()}"
        text = tool_text_for(tool_name, tool_args)
        if hasattr(self.breaker, "observe"):
            self.breaker.observe(text)
        if intent_vector is None:
            intent_vector = intent_vector_for(tool_args)
        self._pending[action_id] = EfferenceCopy(
            action_id=action_id,
            timestamp_ns=time.monotonic_ns(),
            intent_vector=np.asarray(intent_vector, dtype=float),
            tool_name=tool_name,
            tool_args=dict(tool_args),
        )
        banned = set()
        if self.taboo is not None:
            banned = set(self.taboo.active()) & tokenize(text)
        if banned:
            return {
                "allowed": False,
                "reason": f"taboo tokens blocked: {sorted(banned)}",
                "action_id": action_id,
            }
        return {"allowed": True, "reason": "nominal", "action_id": action_id}

    def post_tool_call(self, tool_name: str, tool_result: dict, latency_ms: float) -> str:
        """Captures afferent feedback A(t), solves ODE step, returns suffix."""
        action_ids = [a for a, e in self._pending.items() if e.tool_name == tool_name]
        if not action_ids:
            raise KeyError(f"post_tool_call without pre_tool_call for {tool_name!r}")
        eff = self._pending.pop(action_ids[-1])
        action_id = eff.action_id
        aff = AfferentFeedback(
            action_id=action_id,
            timestamp_ns=eff.timestamp_ns + int(latency_ms * 1e6),
            outcome_vector=intent_vector_for(tool_result),
            status=str(tool_result.get("status", "ok")),
        )
        report = self.comparator.compare(eff, aff)
        self.last_report = report
        current = self.daemon.get_state().current
        if isinstance(tool_result.get("current"), (int, float)):
            current = float(tool_result["current"])
        self.daemon.set_inputs(mismatch=report["spatial_delta"], current=current)
        self.daemon.step_once(max(latency_ms / 1000.0, 1e-3))
        return format_suffix(self.daemon.get_state())

    def intercept_cycle(self, state) -> dict | None:
        """Returns cached CPG routine if habit conditions are met (0 tokens)."""
        if self.habit is None:
            return None
        verdict = self.habit.step(state, breaker_tripped=self.breaker.tripped)
        if verdict.escalate:
            return None
        return self.habit.routine_call(verdict.routine)
