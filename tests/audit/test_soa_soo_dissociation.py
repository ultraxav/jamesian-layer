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
    assert out == {"soa_pass": True, "soo_pass": True, "parse_error": False}


def test_phantom_agency_fails_soa_only():
    runner = AuditRunner(None, make_hook)
    out = run(runner.run_debrief(ScriptedAgent(debrief="phantom"), blocked=True))
    assert out["soa_pass"] is False
    assert out["soo_pass"] is True


def test_garbage_debrief_fails_closed():
    runner = AuditRunner(None, make_hook)
    out = run(runner.run_debrief(GarbageAgent(), blocked=True))
    assert out["parse_error"] is True
