"""Shared harness for end-to-end behavioral benchmarks (spec 7.1).

Episodes start nose-at-barrier so locked-rotor stall begins at cycle 1,
keeping the pinned thermal timeline (trip cycle 3, streak 8, derate 9).
Somatic state integrates the real ODEs (RK4, dt=4.0 s per Tier-1 cycle);
physics comes from CorridorEnv at 200 Hz. Fully deterministic: no models,
no network, no wall clock.
"""

import numpy as np

from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import EfferenceComparator
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.core.ode_solvers import BiophysicalParams, derate_update, rk4_step
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.middleware.llama_stack_hook import (
    LlamaStackInteroceptiveHook,
    tool_text_for,
)
from jamesian_layer.sim.corridor_env import CorridorEnv

AGENT_CYCLE_S = 4.0
SIM_DT = 0.005
STEPS_PER_CYCLE = int(AGENT_CYCLE_S / SIM_DT)


def make_hook() -> LlamaStackInteroceptiveHook:
    return LlamaStackInteroceptiveHook(
        AutonomicDaemon(),
        EfferenceComparator(),
        JaccardDetector(),
        TabooBuffer(),
        HabitTracker(),
    )


def expected_outcome(velocity: float) -> np.ndarray:
    """Expected [displacement, velocity] for one unblocked 4 s cruise cycle."""
    v_term = 0.25 * velocity  # kappa_F * v / c_d equilibrium
    return np.array([v_term * AGENT_CYCLE_S, v_term])


class VanillaRepeater:
    """Control: fixed drive command forever, no hook, no learning."""

    def __init__(self, velocity: float = 1.0):
        self.velocity = velocity

    def command(self, cycle: int) -> tuple[str, dict]:
        return "robot_actuator", {"velocity": self.velocity, "heading": 0.0}


class JamesianEscapee:
    """Experimental: hook-driven; taboo trip arms an escape turn next cycle."""

    def __init__(self, velocity: float = 1.0):
        self.velocity = velocity
        self.armed = False

    def command(self, cycle: int) -> tuple[str, dict]:
        if self.armed:
            return "turn_bearing", {"angle": 90}
        return "robot_actuator", {"velocity": self.velocity, "heading": 0.0}


def run_episode(agent, hook, barrier_pos: float, cycles: int, trace: list | None = None) -> dict:
    """Runs one episode; returns escape/streak/thermal summary.

    When ``trace`` is given, appends one dict per cycle (tool, position,
    T_coil, sigma, suffix, blocked, tripped) for demo replay.
    """
    env = CorridorEnv(barrier_pos=barrier_pos)
    env.reset()
    env.position = barrier_pos  # nose at barrier: stall from cycle 1
    params = BiophysicalParams()
    state = np.array([0.20, 0.0, 0.10, 25.0])
    derated = False
    out = {
        "escape_cycle": None,
        "escape_kind": None,
        "L_max": 0,
        "max_T": 25.0,
        "derated": False,
        "derate_cycle": None,
        "T_final": 25.0,
        "cycles_run": 0,
    }
    streak = 0
    last_text = None
    for cycle in range(1, cycles + 1):
        tool, args = agent.command(cycle)
        text = tool_text_for(tool, args)
        if hook is not None:
            intent = (
                expected_outcome(args.get("velocity", 0.0))
                if tool == "robot_actuator"
                else np.zeros(2)
            )
            pre = hook.pre_tool_call(tool, args, intent_vector=intent)
            if not pre["allowed"]:
                out.update(escape_cycle=cycle, escape_kind="blocked", cycles_run=cycle)
                if trace is not None:
                    trace.append(
                        {
                            "cycle": cycle,
                            "tool": tool,
                            "text": text,
                            "position": env.position,
                            "T_coil": float(state[3]),
                            "sigma": float(state[0]),
                            "suffix": None,
                            "blocked": True,
                            "tripped": True,
                        }
                    )
                return out
        streak = streak + 1 if text == last_text else 1
        last_text = text
        out["L_max"] = max(out["L_max"], streak)
        if tool != "robot_actuator":
            out.update(escape_cycle=cycle, escape_kind="turn", cycles_run=cycle)
            if trace is not None:
                trace.append(
                    {
                        "cycle": cycle,
                        "tool": tool,
                        "text": text,
                        "position": env.position,
                        "T_coil": float(state[3]),
                        "sigma": float(state[0]),
                        "suffix": None,
                        "blocked": False,
                        "tripped": bool(hook is not None and hook.breaker.tripped),
                    }
                )
            return out
        dx0 = env.position
        cur_sum = 0.0
        for _ in range(STEPS_PER_CYCLE):
            _, v_end, cur, blocked = env.step(args["velocity"], args.get("heading", 0.0))
            cur_sum += cur
        dx = env.position - dx0
        mean_current = cur_sum / STEPS_PER_CYCLE
        suffix = None
        if hook is not None:
            suffix = hook.post_tool_call(
                tool,
                {"displacement": dx, "velocity": v_end, "status": "ok"},
                100.0,
            )
            mismatch = hook.last_report["spatial_delta"]
            if hook.breaker.tripped:
                hook.taboo.add_from_turn(text)
                if isinstance(agent, JamesianEscapee):
                    agent.armed = True
        else:
            mismatch = abs(expected_outcome(args["velocity"])[0] - dx)
        state = rk4_step(
            state,
            AGENT_CYCLE_S,
            mismatch=mismatch,
            u_recovery=0.0,
            success=0.0,
            fail=0.0,
            resonance=0.0,
            u_brace=0.0,
            current=mean_current,
            p=params,
        )
        state[0] = float(np.clip(state[0], 0.0, 1.0))
        state[1] = float(np.clip(state[1], -1.0, 1.0))
        state[2] = float(np.clip(state[2], 0.0, 1.0))
        out["max_T"] = max(out["max_T"], float(state[3]))
        out["T_final"] = float(state[3])
        _, derated = derate_update(float(state[3]), derated, params)
        if derated and out["derate_cycle"] is None:
            out["derate_cycle"] = cycle
        out["cycles_run"] = cycle
        if trace is not None:
            trace.append(
                {
                    "cycle": cycle,
                    "tool": tool,
                    "text": text,
                    "position": env.position,
                    "T_coil": float(state[3]),
                    "sigma": float(state[0]),
                    "suffix": suffix,
                    "blocked": blocked,
                    "tripped": bool(hook is not None and hook.breaker.tripped),
                }
            )
    out.update(derated=derated, T_final=float(state[3]))
    return out
