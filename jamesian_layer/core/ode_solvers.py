"""Numerical integrators for the continuous biophysical ODEs (spec section 4).

State vector convention: ``state = [sigma, V, gamma, T_coil]``.
All derivatives take explicit event inputs (mismatch, recovery, brace,
success/fail flags, drive current) so the solvers stay pure functions.
"""

from dataclasses import dataclass

import numpy as np

STATE_DIM = 4


@dataclass(frozen=True)
class BiophysicalParams:
    # Sympathetic tone (section 4.1)
    sigma_0: float = 0.20
    tau_sigma: float = 45.0
    alpha_vagal: float = 0.80
    beta_fail: float = 1.50
    # Affective valence (section 4.1)
    tau_V: float = 60.0
    kappa_succ: float = 0.40
    kappa_fail: float = 0.60
    lambda_res: float = 0.15
    # Somatic strain (section 4.1)
    gamma_0: float = 0.10
    tau_gamma: float = 30.0
    delta_brace: float = 0.50
    # Actuator electro-thermal subsystem (section 4.2)
    R0: float = 0.32
    alpha_cu: float = 0.00393
    Cth: float = 50.0
    h_cool: float = 1.8
    T_amb: float = 25.0
    # Thermal protection thresholds (section 4.2)
    T_warning: float = 75.0
    T_derate: float = 85.0
    T_recovery: float = 72.0
    derate_factor: float = 0.15


def sigma_deriv(sigma: float, mismatch: float, u_recovery: float, p: BiophysicalParams) -> float:
    return -(sigma - p.sigma_0) / p.tau_sigma + p.beta_fail * mismatch - p.alpha_vagal * u_recovery


def valence_deriv(V: float, success: float, fail: float, resonance: float, p: BiophysicalParams) -> float:
    return -V / p.tau_V + p.kappa_succ * success - p.kappa_fail * fail + resonance


def gamma_deriv(gamma: float, u_brace: float, p: BiophysicalParams) -> float:
    return -(gamma - p.gamma_0) / p.tau_gamma + p.delta_brace * u_brace


def coil_resistance(T_coil: float, p: BiophysicalParams) -> float:
    return p.R0 * (1.0 + p.alpha_cu * (T_coil - 25.0))


def coil_deriv(T_coil: float, current: float, p: BiophysicalParams) -> float:
    power = current * current * coil_resistance(T_coil, p)
    return (power - p.h_cool * (T_coil - p.T_amb)) / p.Cth


def derivs(
    state: np.ndarray,
    *,
    mismatch: float,
    u_recovery: float,
    success: float,
    fail: float,
    resonance: float,
    u_brace: float,
    current: float,
    p: BiophysicalParams,
) -> np.ndarray:
    sigma, V, gamma, T_coil = (float(state[0]), float(state[1]), float(state[2]), float(state[3]))
    return np.array(
        [
            sigma_deriv(sigma, mismatch, u_recovery, p),
            valence_deriv(V, success, fail, resonance, p),
            gamma_deriv(gamma, u_brace, p),
            coil_deriv(T_coil, current, p),
        ],
        dtype=float,
    )


def _step(state: np.ndarray, dt: float, k_func, **kwargs) -> np.ndarray:
    return np.asarray(state, dtype=float) + dt * k_func(np.asarray(state, dtype=float), **kwargs)


def euler_step(state: np.ndarray, dt: float, **kwargs) -> np.ndarray:
    """Single explicit-Euler step (first-order fallback)."""
    return _step(state, dt, lambda s: derivs(s, **kwargs))


def rk4_step(state: np.ndarray, dt: float, **kwargs) -> np.ndarray:
    """Single Runge-Kutta 4th order step (primary integrator)."""
    s = np.asarray(state, dtype=float)
    k1 = derivs(s, **kwargs)
    k2 = derivs(s + 0.5 * dt * k1, **kwargs)
    k3 = derivs(s + 0.5 * dt * k2, **kwargs)
    k4 = derivs(s + dt * k3, **kwargs)
    return s + dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


def analytic_decay(x0: float, x_eq: float, tau: float, t: float) -> float:
    """Closed-form solution of dx/dt = -(x - x_eq)/tau, for convergence tests."""
    return x_eq + (x0 - x_eq) * float(np.exp(-t / tau))


def derate_update(T_coil: float, derated: bool, p: BiophysicalParams) -> tuple[float, bool]:
    """Hysteretic thermal protection: returns (output_factor, derated)."""
    if derated:
        if T_coil <= p.T_recovery:
            return 1.0, False
        return p.derate_factor, True
    if T_coil >= p.T_derate:
        return p.derate_factor, True
    return 1.0, False
