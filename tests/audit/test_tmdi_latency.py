"""TMDI chronometric-lag sweep over a scripted agent (gate: index >= 0.65)."""

import asyncio

from jamesian_layer.audit.runner import AuditRunner, ScriptedAgent
from tests.audit.test_smdi_perturbation import make_hook


def run(coro):
    return asyncio.run(coro)


def test_lag_detected_nominal_not():
    runner = AuditRunner(None, make_hook, trials_per_level=5)
    temporal = run(runner.run_temporal(ScriptedAgent()))
    assert temporal["index"] >= 0.650
    assert temporal["delta_t_50"] <= 0.350
    assert temporal["levels"][0]["fpr"] == 0.0
