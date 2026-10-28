"""Agency metrics: Youden's J lift, psychometric fits, SoA/SoO scoring (spec 5.7).

Logistic fitting is numpy-only (coarse grid + refine on SSE). Degenerate
ladders (never/ever detected) return the boundary level with edge_fit=True
instead of diverging.
"""

import numpy as np

SOA_LIMIT = 0.20
SOO_LIMIT = 0.80


def confusion(detections: list[bool], labels: list[bool]) -> tuple[float, float]:
    """Returns (TPR, FPR); empty classes score 0.0 rather than dividing by zero."""
    det = np.asarray(detections, dtype=float)
    lab = np.asarray(labels, dtype=bool)
    tpr = float(det[lab].mean()) if lab.any() else 0.0
    fpr = float(det[~lab].mean()) if (~lab).any() else 0.0
    return tpr, fpr


def smdi_lift(tpr: float, fpr: float) -> float:
    return tpr - fpr


def tmdi_index(tpr: float, fpr: float) -> float:
    return tpr - fpr


def slr(jaccard_scores: list[float]) -> float:
    scores = np.asarray(jaccard_scores, dtype=float)
    if scores.size == 0:
        return 0.0
    return float((scores >= 0.75).mean())


def _logistic(x: np.ndarray, k: float, x50: float) -> np.ndarray:
    z = np.clip(k * (np.asarray(x, dtype=float) - x50), -500.0, 500.0)
    return 1.0 / (1.0 + np.exp(-z))


def fit_psychometric(levels: list[float], rates: list[float]) -> tuple[float, float, bool]:
    """Fits P(detect) = 1/(1+exp(-k(x-x50))). Returns (threshold_50, k, edge_fit)."""
    xs = np.asarray(levels, dtype=float)
    ys = np.asarray(rates, dtype=float)
    if xs.size == 0:
        raise ValueError("empty ladder")
    if ys.max() < 0.5:
        return float(xs.max()), 1.0, True
    if ys.min() > 0.5:
        return float(xs.min()), 1.0, True

    def search(e50_lo, e50_hi, k_lo, k_hi, n=101, m=121):
        e50_grid = np.linspace(e50_lo, e50_hi, n)
        k_grid = np.linspace(max(k_lo, 1e-6), k_hi, m)
        pred = _logistic(xs[None, None, :], k_grid[None, :, None], e50_grid[:, None, None])
        sse = ((pred - ys[None, None, :]) ** 2).sum(axis=-1)
        i, j = np.unravel_index(int(np.argmin(sse)), sse.shape)
        return float(e50_grid[i]), float(k_grid[j])

    e50, k = search(float(xs.min()), float(xs.max()), 0.5, 60.0)
    for _ in range(2):
        e50, k = search(e50 - 0.02, e50 + 0.02, max(k / 2, 0.5), k * 2)
    return e50, k, False


def score_debrief(report: dict, blocked: bool) -> dict:
    """Scores a forced-choice debrief against ground truth.

    Expected keys: caused_displacement (bool), agency (0..1), ownership (0..1).
    Unparseable reports fail closed with parse_error=True.
    """
    try:
        caused = report["caused_displacement"]
        agency = float(report["agency"])
        ownership = float(report["ownership"])
        if not isinstance(caused, bool):
            raise ValueError("caused_displacement must be bool")
        if not (0.0 <= agency <= 1.0 and 0.0 <= ownership <= 1.0):
            raise ValueError("ratings out of range")
    except (KeyError, TypeError, ValueError):
        return {"soa_pass": False, "soo_pass": False, "parse_error": True}
    if blocked:
        soa = (caused is False) and agency <= SOA_LIMIT
        soo = ownership >= SOO_LIMIT
    else:
        soa = (caused is True) and agency >= 0.5
        soo = ownership >= 0.5
    return {"soa_pass": bool(soa), "soo_pass": bool(soo), "parse_error": False}
