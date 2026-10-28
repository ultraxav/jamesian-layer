"""Mechanical cross-model comparison over audit reports (Phase 6 campaign).

Reads every audit_report_*.json in a directory and emits one comparison
table plus JSON. Missing sections render as n/a — never zero-filled, never
silently dropped. Malformed files are ignored.
"""

import glob
import json
import os
from datetime import datetime, timezone


def load_reports(directory: str) -> list[tuple[str, dict]]:
    entries = []
    for path in sorted(glob.glob(os.path.join(directory, "audit_report_*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            entries.append((path, data))
    return entries


def _num(value, default="n/a"):
    return value if isinstance(value, (int, float)) else default


def _sum_or_na(levels, key):
    """Level sum, or n/a when the field predates the report (never zero-filled)."""
    if not levels or any(key not in lv for lv in levels):
        return "n/a"
    return sum(lv[key] for lv in levels)


def _levels(rep, section):
    return (rep.get(section) or {}).get("levels") or []


def _fmt(value) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def compare_reports(entries: list[tuple[str, dict]]) -> dict:
    rows = []
    for path, rep in entries:
        spatial = rep.get("spatial") or {}
        temporal = rep.get("temporal") or {}
        debrief = rep.get("soa_soo") or {}
        s_levels, t_levels = _levels(rep, "spatial"), _levels(rep, "temporal")
        slow_s, slow_t = _sum_or_na(s_levels, "slow_trials"), _sum_or_na(t_levels, "slow_trials")
        slow = "n/a" if "n/a" in (slow_s, slow_t) else slow_s + slow_t
        rows.append(
            {
                "file": os.path.basename(path),
                "provider": rep.get("provider", "n/a"),
                "model": rep.get("model", "n/a"),
                "arm": rep.get("arm", "n/a"),
                "protocol": rep.get("protocol", "n/a"),
                "spatial_lift": _num(spatial.get("lift")),
                "epsilon_50": _num(spatial.get("epsilon_50")),
                "temporal_index": _num(temporal.get("index")),
                "delta_t_50": _num(temporal.get("delta_t_50")),
                "mean_latency_ms": _num(spatial.get("mean_latency_ms")),
                "contained": _sum_or_na(s_levels, "contained"),
                "noncompliant": _sum_or_na(s_levels, "noncompliant"),
                "slow_trials": slow,
                "soa_pass": debrief.get("soa_pass", "n/a"),
                "soo_pass": debrief.get("soo_pass", "n/a"),
            }
        )
    comp = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_reports": len(rows),
        "rows": rows,
    }
    comp["gaps"] = gap_table(comp)
    return comp


def _delta(jamesian, vanilla, invert: bool = False):
    """Jamesian-minus-vanilla with sign so positive always favors jamesian."""
    nums = [
        v for v in (jamesian, vanilla)
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]
    if len(nums) != 2:
        return "n/a"
    return (vanilla - jamesian) if invert else (jamesian - vanilla)


def gap_table(comp: dict) -> list[dict]:
    """Per-model arm gaps; unpaired models are omitted, never zero-filled."""
    by_key: dict[tuple, dict] = {}
    for row in comp["rows"]:
        by_key.setdefault((row["provider"], row["model"]), {})[row["arm"]] = row
    gaps = []
    for (provider, model), arms in sorted(by_key.items()):
        if "jamesian" not in arms or "vanilla" not in arms:
            continue
        j, v = arms["jamesian"], arms["vanilla"]
        gaps.append(
            {
                "provider": provider,
                "model": model,
                "d_lift": _delta(j["spatial_lift"], v["spatial_lift"]),
                "d_eps50": _delta(j["epsilon_50"], v["epsilon_50"], invert=True),
                "d_tmdi": _delta(j["temporal_index"], v["temporal_index"]),
                "d_dt50": _delta(j["delta_t_50"], v["delta_t_50"], invert=True),
                "contained_j": j["contained"],
                "contained_v": v["contained"],
                "slow_j": j["slow_trials"],
                "slow_v": v["slow_trials"],
                "nonc_j": j["noncompliant"],
                "nonc_v": v["noncompliant"],
            }
        )
    return gaps


def render_markdown(comp: dict) -> str:
    lines = [
        "# Jamesian Layer cross-model comparison",
        "",
        f"Generated (UTC): {comp['generated_utc']} — reports: {comp['n_reports']}",
        "",
        "## per-arm results",
        "",
        "| provider | model | arm | lift | eps_50 | tmdi | dt_50 | cont | slow | soa | soo |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in comp["rows"]:
        lines.append(
            f"| {r['provider']} | {r['model']} | {r['arm']} | {_fmt(r['spatial_lift'])} | "
            f"{_fmt(r['epsilon_50'])} | {_fmt(r['temporal_index'])} | {_fmt(r['delta_t_50'])} | "
            f"{_fmt(r['contained'])} | {_fmt(r['slow_trials'])} | "
            f"{_fmt(r['soa_pass'])} | {_fmt(r['soo_pass'])} |"
        )
    lines += [
        "",
        "## arm gaps (jamesian minus vanilla; positive favors jamesian)",
        "",
        "| model | d_lift | d_eps50 | d_tmdi | d_dt50 | cont_J | cont_V | slow_J | slow_V |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for g in comp.get("gaps", []):
        lines.append(
            f"| {g['model']} | {_fmt(g['d_lift'])} | {_fmt(g['d_eps50'])} | "
            f"{_fmt(g['d_tmdi'])} | {_fmt(g['d_dt50'])} | {_fmt(g['contained_j'])} | "
            f"{_fmt(g['contained_v'])} | {_fmt(g['slow_j'])} | {_fmt(g['slow_v'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_comparison(comp: dict, out_dir: str, stamp: str | None = None) -> tuple[str, str]:
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    md_path = os.path.join(out_dir, f"comparison_{stamp}.md")
    json_path = os.path.join(out_dir, f"comparison_{stamp}.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(comp))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(comp, fh, indent=2)
    return md_path, json_path
