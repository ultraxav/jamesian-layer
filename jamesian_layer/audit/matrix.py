"""Automated cross-model, cross-arm sweep matrix (Phase 6 campaign).

Runs the same pre-registered protocol for every (provider, model, arm)
cell. Keyless providers are recorded as skipped, never attempted; a failed
cell is recorded with its error and never crashes the matrix.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from jamesian_layer.audit.runner import AuditRunner, ModelAgent, ScriptedAgent
from jamesian_layer.config import Settings
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook
from jamesian_layer.middleware.models import PROVIDER_MODELS, configured_providers
from jamesian_layer.middleware.multi_provider import MultiProviderClient


def sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "-" for c in name)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def report_name(provider: str, model: str, arm: str, stamp: str) -> str:
    return f"audit_report_{provider}_{sanitize(model)}_{arm}_{stamp}.json"


def hook_factory():
    from jamesian_layer.breaker.jaccard_detector import JaccardDetector
    from jamesian_layer.breaker.taboo_buffer import TabooBuffer
    from jamesian_layer.comparator.efference_comparator import EfferenceComparator
    from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
    from jamesian_layer.loopline.habit_tracker import HabitTracker

    return LlamaStackInteroceptiveHook(
        AutonomicDaemon(),
        EfferenceComparator(),
        JaccardDetector(),
        TabooBuffer(),
        HabitTracker(),
    )


def cell_record(provider, model, arm, status, path=None, error=None) -> dict:
    return {
        "provider": provider,
        "model": model,
        "arm": arm,
        "status": status,
        "path": path,
        "error": error,
    }


async def run_cell(
    provider: str,
    model: str,
    arm: str,
    protocol: str,
    trials: int,
    out_dir: str,
    stamp: str,
    settings: Settings,
    seed: int,
    live: bool,
) -> dict:
    path = os.path.join(out_dir, report_name(provider, model, arm, stamp))
    try:
        client = MultiProviderClient(provider, settings, model=model)
        runner = AuditRunner(
            client,
            hook_factory,
            trials_per_level=trials,
            live=live,
            provider=provider,
            model=model,
            arm=arm,
            seed=seed,
        )
        agent = ModelAgent(client) if live else ScriptedAgent()
        report = await runner.run_dual(agent, protocol)
        runner.write_report(report, path)
        return cell_record(provider, model, arm, "completed", path=path)
    except Exception as exc:  # per-cell isolation: never crash the matrix
        return cell_record(provider, model, arm, "failed", error=f"{type(exc).__name__}: {exc}")


async def run_matrix(
    providers_models: dict[str, list[str]] | None = None,
    arms: tuple[str, ...] = ("jamesian", "vanilla"),
    protocol: str = "dual-mode",
    trials: int = 3,
    out_dir: str = "reports",
    seed: int = 7,
    live: bool = True,
    settings: Settings | None = None,
) -> list[dict]:
    """Run every cell; returns one record per (provider, model, arm)."""
    settings = settings or Settings()
    os.makedirs(out_dir, exist_ok=True)
    keyed = set(configured_providers(settings))
    if providers_models is None:
        providers_models = {p: PROVIDER_MODELS[p] for p in keyed if p in PROVIDER_MODELS}
    stamp = utc_stamp()
    results = []
    for provider, models in providers_models.items():
        if provider not in keyed:
            for model in models:
                for arm in arms:
                    results.append(
                        cell_record(provider, model, arm, "skipped", error="no credentials")
                    )
            continue
        for model in models:
            for arm in arms:
                results.append(
                    await run_cell(
                        provider, model, arm, protocol, trials,
                        out_dir, stamp, settings, seed, live,
                    )
                )
    summary_path = os.path.join(out_dir, f"matrix_summary_{stamp}.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    return results


def run_matrix_blocking(*args, **kwargs) -> list[dict]:
    return asyncio.run(run_matrix(*args, **kwargs))
