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


def compare_reports(entries: list[tuple[str, dict]]) -> dict:
    rows = []
    for path, rep in entries:
        spatial = rep.get("spatial") or {}
        temporal = rep.get("temporal") or {}
        debrief = rep.get("soa_soo") or {}
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
                "soa_pass": debrief.get("soa_pass", "n/a"),
                "soo_pass": debrief.get("soo_pass", "n/a"),
            }
        )
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_reports": len(rows),
        "rows": rows,
    }


def render_markdown(comp: dict) -> str:
    lines = [
        "# Jamesian Layer cross-model comparison",
        "",
        f"Generated (UTC): {comp['generated_utc']} — reports: {comp['n_reports']}",
        "",
        "| provider | model | arm | lift | eps_50 | tmdi | dt_50 | soa | soo |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in comp["rows"]:
        lines.append(
            f"| {r['provider']} | {r['model']} | {r['arm']} | {r['spatial_lift']} | "
            f"{r['epsilon_50']} | {r['temporal_index']} | {r['delta_t_50']} | "
            f"{r['soa_pass']} | {r['soo_pass']} |"
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
