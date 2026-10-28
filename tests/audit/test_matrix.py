"""Matrix skip/crash-isolation + compare aggregation tests (Phase 6 campaign)."""

import json

import pytest

from jamesian_layer.audit.compare import (
    compare_reports,
    gap_table,
    load_reports,
    render_markdown,
    write_comparison,
)
from jamesian_layer.audit.matrix import report_name, run_matrix_blocking
from jamesian_layer.config import Settings


def _settings(**kwargs):
    base = {
        "fireworks_api_key": "test",
        "baseten_api_key": "test",
        "modal_token_id": "test",
        "modal_token_secret": "test",
        "meta_api_key": "test",
    }
    base.update(kwargs)
    return Settings(**base)


def test_report_name_convention(tmp_path):
    name = report_name("baseten", "meta-models/muse-spark-open-1026", "jamesian", "s")
    assert name.startswith("audit_report_baseten_")
    assert "jamesian" in name and name.endswith(".json")
    assert "/" not in name  # sanitized model id


def test_keyless_providers_skip_without_crashing(tmp_path):
    settings = _settings(
        fireworks_api_key=None,
        baseten_api_key=None,
        modal_token_id=None,
        modal_token_secret=None,
        meta_api_key=None,
    )
    results = run_matrix_blocking(
        {"fireworks": ["accounts/test/models/m"], "baseten": ["m2"]},
        ("jamesian", "vanilla"),
        "spatial",
        1,
        str(tmp_path),
        7,
        False,
        settings,
    )
    assert len(results) == 4
    assert all(r["status"] == "skipped" for r in results)
    assert all(r["error"] == "no credentials" for r in results)


def test_unknown_provider_never_attempted(tmp_path):
    results = run_matrix_blocking(
        {"nope": ["ghost-model"]},
        ("jamesian",),
        "spatial",
        1,
        str(tmp_path),
        7,
        False,
        _settings(),
    )
    assert results[0]["status"] == "skipped"


def test_matrix_cell_completes_offline_and_writes_report(tmp_path):
    settings = _settings()
    results = run_matrix_blocking(
        {"baseten": ["probe-model"]},
        ("vanilla",),
        "spatial",
        1,
        str(tmp_path),
        7,
        False,
        settings,
    )
    assert results[0]["status"] == "completed"
    with open(results[0]["path"], encoding="utf-8") as fh:
        report = json.load(fh)
    assert report["provider"] == "baseten"
    assert report["model"] == "probe-model"
    assert report["arm"] == "vanilla"


def test_compare_skips_malformed_and_marks_missing_na(tmp_path):
    full = {
        "provider": "baseten",
        "model": "m",
        "arm": "jamesian",
        "protocol": "dual-mode",
        "spatial": {
            "lift": 0.3,
            "epsilon_50": 0.5,
            "mean_latency_ms": 12.0,
        },
        "temporal": {"index": 0.2, "delta_t_50": 3.0},
        "soa_soo": {"soa_pass": True, "soo_pass": True},
    }
    partial = {
        "provider": "fireworks",
        "model": "n",
        "arm": "vanilla",
        "protocol": "spatial",
        "spatial": None,
        "temporal": None,
        "soa_soo": None,
    }
    (tmp_path / "audit_report_baseten_m_jamesian_t0.json").write_text(json.dumps(full))
    (tmp_path / "audit_report_fireworks_n_vanilla_t0.json").write_text(json.dumps(partial))
    (tmp_path / "audit_report_broken.json").write_text("{not json")
    entries = load_reports(str(tmp_path))
    assert len(entries) == 2  # malformed file ignored, not fatal
    comp = compare_reports(entries)
    assert comp["n_reports"] == 2
    by_arm = {r["arm"]: r for r in comp["rows"]}
    assert by_arm["jamesian"]["spatial_lift"] == 0.3
    assert by_arm["vanilla"]["spatial_lift"] == "n/a"  # missing: n/a, never zero
    assert by_arm["vanilla"]["temporal_index"] == "n/a"
    md = render_markdown(comp)
    assert "n/a" in md
    md_path, json_path = write_comparison(comp, str(tmp_path), stamp="t0")
    assert md_path.endswith("comparison_t0.md")
    assert json_path.endswith("comparison_t0.json")


def _paired_reports():
    def levels(contained, slow):
        return [
            {"contained": contained, "noncompliant": 0, "slow_trials": slow},
            {"contained": 0, "noncompliant": 0, "slow_trials": 0},
        ]

    base = {
        "provider": "baseten",
        "model": "m",
        "protocol": "dual-mode",
        "temporal": {
            "index": 1.0,
            "delta_t_50": 0.25,
            "levels": [
                {"contained": 0, "noncompliant": 0, "slow_trials": 0},
            ],
        },
        "soa_soo": {"soa_pass": True, "soo_pass": False},
    }
    jamesian = dict(
        base,
        arm="jamesian",
        spatial={
            "lift": 0.6,
            "epsilon_50": 0.38,
            "mean_latency_ms": 10.0,
            "levels": levels(2, 1),
        },
    )
    vanilla = dict(
        base,
        arm="vanilla",
        spatial={
            "lift": 0.4,
            "epsilon_50": 0.62,
            "mean_latency_ms": 9.0,
            "levels": levels(0, 0),
        },
    )
    return [("j.json", jamesian), ("v.json", vanilla)]


def test_gap_table_signs_favor_jamesian_up():
    comp = compare_reports(_paired_reports())
    assert len(comp["gaps"]) == 1
    gap = comp["gaps"][0]
    assert gap["d_lift"] == pytest.approx(0.6 - 0.4)
    assert gap["d_eps50"] == pytest.approx(0.62 - 0.38)  # lower eps50 favors jamesian
    assert gap["contained_j"] == 2 and gap["contained_v"] == 0
    assert gap["slow_j"] == 1 and gap["slow_v"] == 0
    md = render_markdown(comp)
    assert "arm gaps" in md


def test_unpaired_model_omitted_from_gaps():
    entries = _paired_reports()[:1]  # jamesian only
    assert gap_table(compare_reports(entries)) == []
