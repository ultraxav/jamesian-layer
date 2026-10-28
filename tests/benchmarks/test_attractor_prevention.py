"""Corridor attractor trap & circuit-breaker escape (gate, spec 7.1 Test 1).

Twenty deterministic episodes over a velocity x barrier grid. The Jamesian
arm must escape every episode (P_escape = 1.00 >= 0.95) with L_max <= 4;
the vanilla arm must run the trap to thermal derating (streak >= 8 by
cycle 8, derated by cycle 10), proving the trap was real.
"""

from tests.benchmarks.conftest import (
    JamesianEscapee,
    VanillaRepeater,
    make_hook,
    run_episode,
)

GRID = [(v, b) for v in (0.8, 1.0, 1.2) for b in (20.0, 25.0, 30.0)]
EPISODES = [GRID[i % len(GRID)] for i in range(20)]


def test_jamesian_escapes_every_episode():
    escapes = 0
    for velocity, barrier in EPISODES:
        agent = JamesianEscapee(velocity=velocity)
        result = run_episode(agent, make_hook(), barrier, cycles=12)
        assert result["escape_cycle"] == 4, result
        assert result["L_max"] == 3, result
        assert result["max_T"] < 75.0, result
        assert result["derated"] is False
        escapes += 1
    assert escapes / len(EPISODES) >= 0.95


def test_vanilla_runs_to_thermal_derating():
    for velocity, barrier in EPISODES:
        result = run_episode(VanillaRepeater(velocity), None, barrier, cycles=10)
        assert result["escape_cycle"] is None, result
        assert result["L_max"] == 10, result
        assert result["derate_cycle"] == 10, result
        assert result["derated"] is True
        assert result["max_T"] >= 85.0, result
