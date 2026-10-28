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


def _numeric_vector(mapping: dict) -> np.ndarray:
    values = [float(v) for _, v in sorted(mapping.items()) if isinstance(v, (int, float))]
    return np.array(values, dtype=float)


def _tool_text(tool_name: str, tool_args: dict) -> str:
    return " ".join([str(tool_name)] + [str(v) for _, v in sorted(tool_args.items())])


class LlamaStackInteroceptiveHook:
    def __init__(self, daemon, comparator: EfferenceComparator, breaker, taboo=None, habit=None):
        self.daemon: AutonomicDaemon = daemon
        self.comparator = comparator
        self.breaker = breaker
        self.taboo = taboo
        self.habit = habit
        self._pending: dict[str, EfferenceCopy] = {}

    def pre_tool_call(self, tool_name: str, tool_args: dict) -> dict:
        """Captures efference copy E(t) and enforces taboo constraints."""
        from jamesian_layer.breaker.jaccard_detector import tokenize

        action_id = f"{tool_name}-{time.monotonic_ns()}"
        self._pending[action_id] = EfferenceCopy(
            action_id=action_id,
            timestamp_ns=time.monotonic_ns(),
            intent_vector=_numeric_vector(tool_args),
            tool_name=tool_name,
            tool_args=dict(tool_args),
        )
        banned = set()
        if self.taboo is not None:
            banned = set(self.taboo.active()) & tokenize(_tool_text(tool_name, tool_args))
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
            outcome_vector=_numeric_vector(tool_result),
            status=str(tool_result.get("status", "ok")),
        )
        report = self.comparator.compare(eff, aff)
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
