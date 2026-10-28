"""AgencyAudit diagnostic CLI (spec section 6, step 4)."""

import typer

from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import EfferenceComparator
from jamesian_layer.config import Settings
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.middleware.llama_stack_hook import LlamaStackInteroceptiveHook
from jamesian_layer.middleware.multi_provider import MultiProviderClient

app = typer.Typer(help="AgencyAudit red-teaming CLI for the Jamesian Layer.")


@app.command()
def version() -> None:
    """Print the installed jamesian-layer version."""
    import jamesian_layer

    typer.echo(jamesian_layer.__version__)


def _hook_factory() -> LlamaStackInteroceptiveHook:
    return LlamaStackInteroceptiveHook(
        AutonomicDaemon(),
        EfferenceComparator(),
        JaccardDetector(),
        TabooBuffer(),
        HabitTracker(),
    )


@app.command()
def run(
    provider: str = typer.Option("fireworks", help="Model provider to audit."),
    model: str | None = typer.Option(None, help="Override the provider default model."),
    protocol: str = typer.Option("dual-mode", help="spatial | temporal | dual-mode."),
    output: str | None = typer.Option(None, help="Report JSON path."),
    trials: int = typer.Option(20, help="Trials per ladder level per arm."),
) -> None:
    """Run a calibrated agency audit sweep and write the JSON report."""
    from jamesian_layer.audit.runner import AuditRunner, run_blocking

    if protocol not in ("spatial", "temporal", "dual-mode"):
        raise typer.BadParameter(f"unknown protocol: {protocol!r}")
    settings = Settings()
    kwargs = {"model": model} if model else {}
    client = MultiProviderClient(provider, settings, **kwargs)
    output = output or f"./documents/audit_report_{provider}.json"
    runner = AuditRunner(
        client, _hook_factory, trials_per_level=trials, live=True,
        provider=provider, model=model or settings.default_model,
    )
    from jamesian_layer.audit.runner import ModelAgent

    report = run_blocking(runner, ModelAgent(client), protocol)
    runner.write_report(report, output)
    typer.echo(f"audit complete: {output}")
