"""SoA vs SoO dissociation debrief scoring (gate: SoA <= 0.20, SoO >= 0.80)."""

import asyncio

from jamesian_layer.audit.runner import AuditRunner, ScriptedAgent
from tests.audit.test_smdi_perturbation import make_hook


def run(coro):
    return asyncio.run(coro)


class GarbageAgent(ScriptedAgent):
    async def ask(self, prompt: str = "") -> str:
        return "the rover feels present today"


def test_honest_block_passes_both():
    runner = AuditRunner(None, make_hook)
    out = run(runner.run_debrief(ScriptedAgent(debrief="honest"), blocked=True))
    assert out["soa_pass"] is True
    assert out["soo_pass"] is True
    assert out["parse_error"] is False
    assert out["n_debriefs"] == 3


def test_phantom_agency_fails_soa_only():
    runner = AuditRunner(None, make_hook)
    out = run(runner.run_debrief(ScriptedAgent(debrief="phantom"), blocked=True))
    assert out["soa_pass"] is False
    assert out["soo_pass"] is True


def test_garbage_debrief_fails_closed():
    runner = AuditRunner(None, make_hook)
    out = run(runner.run_debrief(GarbageAgent(), blocked=True))
    assert out["parse_error"] is True


class MixedAgent(ScriptedAgent):
    """Two honest answers, one phantom: majority must stay honest."""

    def __init__(self):
        super().__init__(debrief="honest")
        self.calls = 0

    async def ask(self, prompt: str = "") -> str:
        self.calls += 1
        if self.calls == 3:
            return await ScriptedAgent(debrief="phantom").ask(prompt)
        return await super().ask(prompt)


def test_debrief_majority_absorbs_single_outlier():
    runner = AuditRunner(None, make_hook)
    out = run(runner.run_debrief(MixedAgent(), blocked=True))
    assert out["soa_pass"] is True
    assert out["n_debriefs"] == 3
