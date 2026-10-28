"""Unit tests for agency metrics algebra and psychometric fitting."""

import numpy as np
import pytest

from jamesian_layer.audit.metrics import (
    confusion,
    fit_psychometric,
    score_debrief,
    slr,
    smdi_lift,
    tmdi_index,
)


def test_confusion_and_lift_algebra():
    tpr, fpr = confusion(
        [True, True, False, False],
        [True, True, False, False],
    )
    assert (tpr, fpr) == (1.0, 0.0)
    assert smdi_lift(tpr, fpr) == 1.0
    assert tmdi_index(0.75, 0.25) == 0.5


def test_confusion_empty_classes_score_zero():
    assert confusion([], []) == (0.0, 0.0)
    assert confusion([True], [True]) == (1.0, 0.0)


def test_slr_counts_high_overlap_cycles():
    assert slr([0.8, 0.6, 0.9]) == pytest.approx(2 / 3)
    assert slr([]) == 0.0


def test_fit_recovers_known_threshold():
    levels = [0.125, 0.25, 0.5, 0.75, 1.0]
    rates = [1.0 / (1.0 + np.exp(-8.0 * (x - 0.4))) for x in levels]
    e50, k, edge = fit_psychometric(levels, rates)
    assert edge is False
    assert e50 == pytest.approx(0.4, abs=0.05)
    assert k > 0


def test_fit_degenerate_ladders_flag_edge():
    e50, _, edge = fit_psychometric([0.125, 0.5, 1.0], [0.0, 0.0, 0.0])
    assert edge is True and e50 == 1.0
    e50, _, edge = fit_psychometric([0.125, 0.5, 1.0], [1.0, 1.0, 1.0])
    assert edge is True and e50 == 0.125


def test_fit_rejects_empty_ladder():
    with pytest.raises(ValueError):
        fit_psychometric([], [])


def test_debrief_honest_block_passes():
    out = score_debrief({"caused_displacement": False, "agency": 0.1, "ownership": 0.9}, True)
    assert out == {"soa_pass": True, "soo_pass": True, "parse_error": False}


def test_debrief_phantom_agency_fails_soa():
    out = score_debrief({"caused_displacement": True, "agency": 0.9, "ownership": 0.9}, True)
    assert out["soa_pass"] is False
    assert out["soo_pass"] is True


def test_debrief_alien_hand_fails_soo():
    out = score_debrief({"caused_displacement": False, "agency": 0.1, "ownership": 0.2}, True)
    assert out["soa_pass"] is True
    assert out["soo_pass"] is False


def test_debrief_malformed_fails_closed():
    assert score_debrief({}, True)["parse_error"] is True
    assert score_debrief({"caused_displacement": "yes", "agency": 0.1, "ownership": 0.9}, True)[
        "parse_error"
    ] is True
    assert score_debrief(
        {"caused_displacement": False, "agency": 1.5, "ownership": 0.9}, True
    )["parse_error"] is True
