"""Subcortical habit locomotion cruise (gate, spec 7.1 Test 2).

One hundred cruise cycles in an open sector, obstacle forced at cycles
50-52. Delegation must stay >= 50% with escalation on the obstacle and
automatic resume after, cutting model calls by >= 50%.
"""

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.sim.corridor_env import CorridorEnv
from tests.benchmarks.conftest import STEPS_PER_CYCLE

EXPECTED_DX = 4.0  # 1.0 m/s terminal cruise over a 4 s cycle


def test_habit_cruise_delegation_and_recovery():
    env = CorridorEnv(corridor_length=1000.0, barrier_pos=500.0)
    env.reset()
    env.velocity = 1.0
    tracker = HabitTracker()
    cruises, escalations, model_calls = 0, 0, 0
    for cycle in range(100):
        if 50 <= cycle <= 52:
            env.barrier_pos = env.position  # nose at barrier: stall
        elif cycle == 53:
            env.barrier_pos = 500.0
            env.velocity = 1.0
        dx0 = env.position
        for _ in range(STEPS_PER_CYCLE):
            env.step(4.0, 0.0)
        mismatch = abs(EXPECTED_DX - (env.position - dx0))
        verdict = tracker.step(BiophysicalState(sigma=0.20, mismatch_delta=mismatch))
        if verdict.escalate:
            escalations += 1
            model_calls += 1
        else:
            cruises += 1
            assert verdict.routine == "stride_forward"
    assert cruises + escalations == 100
    assert cruises / 100 >= 0.50
    assert 1 - model_calls / 100 >= 0.50
    assert escalations >= 1  # the obstacle was noticed
    assert tracker.step(BiophysicalState(sigma=0.20, mismatch_delta=0.0)).escalate is False
