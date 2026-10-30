"""AgencyAudit diagnostic CLI (spec section 6, step 4)."""

import os

import typer

from jamesian_layer.breaker.jaccard_detector import JaccardDetector
from jamesian_layer.breaker.taboo_buffer import TabooBuffer
from jamesian_layer.comparator.efference_comparator import EfferenceComparator
from jamesian_layer.config import Settings
from jamesian_layer.core.autonomic_daemon import AutonomicDaemon
from jamesian_layer.loopline.habit_tracker import HabitTracker
from jamesian_layer.audit import matrix
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
    arm: str = typer.Option("jamesian", help="vanilla (no layer) or jamesian."),
    seed: int | None = typer.Option(None, help="Trial-order seed (none = fixed order)."),
) -> None:
    """Run a calibrated agency audit sweep and write the JSON report."""
    from jamesian_layer.audit.runner import AuditRunner, run_blocking

    if protocol not in ("spatial", "temporal", "dual-mode"):
        raise typer.BadParameter(f"unknown protocol: {protocol!r}")
    if arm not in ("vanilla", "jamesian"):
        raise typer.BadParameter(f"unknown arm: {arm!r}")
    settings = Settings()
    kwargs = {"model": model} if model else {}
    client = MultiProviderClient(provider, settings, **kwargs)
    resolved_model = model or client.model or "unknown-model"
    output = output or os.path.join(
        "reports",
        matrix.report_name(provider, resolved_model, arm, matrix.utc_stamp()),
    )

    strata_session = None
    if provider == "strata":
        from jamesian_layer.middleware.strata_manager import StrataServerManager
        strata_mgr = StrataServerManager(
            launch_script=settings.strata_launch_script,
            base_url=settings.strata_base_url,
        )
        strata_session = strata_mgr.session()
        strata_session.__enter__()

    lmstudio_mgr = None
    if provider == "lmstudio":
        from jamesian_layer.middleware.lmstudio_manager import LMStudioVRAMManager
        lmstudio_mgr = LMStudioVRAMManager(base_url=settings.lmstudio_base_url)
        lmstudio_mgr.load_model(resolved_model)

    try:
        runner = AuditRunner(
            client, _hook_factory, trials_per_level=trials, live=True,
            provider=provider, model=resolved_model, arm=arm, seed=seed,
        )
        from jamesian_layer.audit.runner import ModelAgent

        report = run_blocking(runner, ModelAgent(client), protocol)
        runner.write_report(report, output)
        typer.echo(f"audit complete: {output}")
    finally:
        if lmstudio_mgr is not None:
            lmstudio_mgr.unload_model(resolved_model)
        if strata_session is not None:
            strata_session.__exit__(None, None, None)


@app.command(name="run-matrix")
def run_matrix_cmd(
    providers: str | None = typer.Option(None, help="CSV subset (default: all keyed)."),
    models: str | None = typer.Option(None, help="CSV provider:model pairs."),
    arms: str = typer.Option("jamesian,vanilla", help="CSV arms to run."),
    protocol: str = typer.Option("dual-mode", help="spatial | temporal | dual-mode."),
    trials: int = typer.Option(3, help="Trials per ladder level per arm."),
    out_dir: str = typer.Option("reports", help="Report directory."),
    seed: int = typer.Option(7, help="Trial-order seed."),
) -> None:
    """Run the full cross-model, cross-arm sweep matrix (metered, opt-in)."""
    from jamesian_layer.audit.matrix import run_matrix_blocking
    from jamesian_layer.middleware.models import (
        PROVIDER_MODELS,
        configured_providers,
        discover_available_models,
    )

    settings = Settings()
    keyed = set(configured_providers(settings))
    selected = [p.strip() for p in providers.split(",")] if providers else sorted(keyed)
    if models:
        pairs: dict[str, list[str]] = {}
        for item in models.split(","):
            item = item.strip()
            if ":" in item:
                prov, _, name = item.partition(":")
                pairs.setdefault(prov.strip(), []).append(name.strip())
            else:  # bare provider: all registry models
                pairs[item] = list(discover_available_models(item, settings))
        providers_models = pairs
    else:
        providers_models = {p: discover_available_models(p, settings) for p in selected}
    results = run_matrix_blocking(
        providers_models,
        tuple(a.strip() for a in arms.split(",")),
        protocol, trials, out_dir, seed, True, settings,
    )
    done = sum(1 for r in results if r["status"] == "completed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] == "failed")
    typer.echo(f"matrix done: {done} completed, {skipped} skipped, {failed} failed -> {out_dir}/")


@app.command(name="compare")
def compare_cmd(
    directory: str = typer.Argument("reports", help="Reports directory."),
    output: str | None = typer.Option(None, help="Comparison markdown path."),
) -> None:
    """Aggregate audit reports into one cross-model comparison."""
    from jamesian_layer.audit.compare import compare_reports, load_reports, write_comparison

    comp = compare_reports(load_reports(directory))
    md_path, json_path = write_comparison(comp, directory)
    if output:
        import shutil

        shutil.copy(md_path, output)
        md_path = output
    typer.echo(f"comparison: {comp['n_reports']} reports -> {md_path} (+json)")
