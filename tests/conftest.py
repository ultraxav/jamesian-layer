"""Shared pytest fixtures: default params and quiescent somatic state."""

import pytest

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.core.ode_solvers import BiophysicalParams


@pytest.fixture
def params() -> BiophysicalParams:
    return BiophysicalParams()


@pytest.fixture
def state() -> BiophysicalState:
    return BiophysicalState()
