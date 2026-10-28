"""Unit tests for the biophysical ODE solvers (acceptance gate, spec 7.2)."""

import numpy as np

from jamesian_layer.core.ode_solvers import (
    analytic_decay,
    coil_deriv,
    derate_update,
    derivs,
    euler_step,
    rk4_step,
)

ZERO_INPUTS = {
    "mismatch": 0.0,
    "u_recovery": 0.0,
    "success": 0.0,
    "fail": 0.0,
    "resonance": 0.0,
    "u_brace": 0.0,
    "current": 0.0,
}


def _sigma_error(dt: float, params, steps: int = 20) -> float:
    state = np.array([0.80, 0.0, 0.10, 25.0])
    for _ in range(steps):
        state = rk4_step(state, dt, **{**ZERO_INPUTS, "p": params})
    t = dt * steps
    return abs(state[0] - analytic_decay(0.80, params.sigma_0, params.tau_sigma, t))


def test_rk4_convergence_order(params):
    """Halving dt must shrink RK4 error by ~16x (O(dt^4))."""
    err_coarse = _sigma_error(0.5, params)
    err_fine = _sigma_error(0.25, params)
    assert err_coarse > 0
    ratio = err_coarse / err_fine
    assert 8.0 < ratio < 32.0


def test_euler_less_accurate_than_rk4(params):
    """Sanity: first-order Euler trails RK4 on the same decay problem."""
    state_rk4 = np.array([0.80, 0.0, 0.10, 25.0])
    state_euler = state_rk4.copy()
    for _ in range(20):
        state_rk4 = rk4_step(state_rk4, 0.5, **{**ZERO_INPUTS, "p": params})
        state_euler = euler_step(state_euler, 0.5, **{**ZERO_INPUTS, "p": params})
    target = analytic_decay(0.80, params.sigma_0, params.tau_sigma, 10.0)
    assert abs(state_rk4[0] - target) < abs(state_euler[0] - target)


def test_valence_stays_finite_under_sustained_events(params):
    """Sustained failure then success keeps the raw solver finite.

    Bounding to V in [-1, 1] is the state layer's job (BiophysicalState.clamp,
    applied per step by the daemon); the solver must never produce NaN/inf.
    """
    state = np.array([0.20, 0.0, 0.10, 25.0])
    for _ in range(2000):
        state = rk4_step(state, 0.1, **{**ZERO_INPUTS, "fail": 1.0, "p": params})
    assert np.all(np.isfinite(state))
    for _ in range(2000):
        state = rk4_step(state, 0.1, **{**ZERO_INPUTS, "success": 1.0, "p": params})
    assert np.all(np.isfinite(state))


def test_state_clamp_enforces_bounds():
    """BiophysicalState.clamp pins sigma/gamma to [0, 1] and V to [-1, 1]."""
    from jamesian_layer.core.biophysical_state import BiophysicalState

    clamped = BiophysicalState(sigma=2.5, valence=-36.0, gamma=-0.5).clamp()
    assert clamped.sigma == 1.0
    assert clamped.valence == -1.0
    assert clamped.gamma == 0.0


def test_coil_cruise_steady_state(params):
    """4 A cruise settles within 0.5% of the analytic ~27.88 C equilibrium."""
    state = np.array([0.20, 0.0, 0.10, 25.0])
    for _ in range(800):
        state = rk4_step(state, 0.5, **{**ZERO_INPUTS, "current": 4.0, "p": params})
    power = 16.0 * params.R0
    heff = params.h_cool - power * params.alpha_cu
    expected = params.T_amb + power / heff
    assert abs(state[3] - expected) / expected <= 0.005


def test_coil_stall_heat_rises(params):
    """20 A stall must drive the coil hot (derating regime reachable)."""
    assert coil_deriv(25.0, 20.0, params) > 0.0
    state = np.array([0.20, 0.0, 0.10, 25.0])
    for _ in range(800):  # 40 s simulated: past the ~36 s derating point
        state = rk4_step(state, 0.05, **{**ZERO_INPUTS, "current": 20.0, "p": params})
    assert state[3] >= params.T_derate


def test_no_nan_long_mixed_run(params):
    """Mixed cruise/stall/brace/recovery inputs stay finite (no NaN)."""
    state = np.array([0.20, 0.0, 0.10, 25.0])
    schedule = [
        {"current": 4.0},
        {"current": 20.0, "mismatch": 0.9, "fail": 1.0},
        {"current": 0.0, "u_recovery": 1.0, "u_brace": 0.5},
        {"current": 4.0, "success": 1.0},
    ]
    for i in range(4000):
        extra = schedule[(i // 1000) % len(schedule)]
        state = rk4_step(state, 0.05, **{**ZERO_INPUTS, **extra, "p": params})
    assert np.all(np.isfinite(state))


def test_derivate_vector_shape(params):
    out = derivs(np.array([0.2, 0.0, 0.1, 25.0]), **{**ZERO_INPUTS, "p": params})
    assert out.shape == (4,)
    assert np.all(np.isfinite(out))


def test_derate_hysteresis(params):
    assert derate_update(90.0, False, params) == (params.derate_factor, True)
    assert derate_update(80.0, True, params) == (params.derate_factor, True)
    assert derate_update(72.0, True, params) == (1.0, False)
    assert derate_update(25.0, False, params) == (1.0, False)
