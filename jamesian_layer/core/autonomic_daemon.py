"""10-50 Hz asynchronous autonomic daemon (spec section 6, step 1).

Runs the biophysical ODE loop on a background thread with monotonic-clock
timing. Carries no provider imports: it only integrates local state from
event inputs supplied via :meth:`set_inputs` or :meth:`step_once`.
"""

import threading
import time
from collections import deque
from dataclasses import replace

from jamesian_layer.core.biophysical_state import BiophysicalState
from jamesian_layer.core.ode_solvers import BiophysicalParams, rk4_step


class AutonomicDaemon:
    def __init__(
        self,
        params: BiophysicalParams | None = None,
        frequency_hz: float = 20.0,
        history_len: int = 600,
        max_dt_s: float = 0.5,
    ) -> None:
        self.params = params or BiophysicalParams()
        self.frequency_hz = frequency_hz
        self.max_dt_s = max_dt_s
        self._history: deque[BiophysicalState] = deque(maxlen=history_len)
        self._state = BiophysicalState()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._inputs: dict = {
            "mismatch": 0.0,
            "u_recovery": 0.0,
            "success": 0.0,
            "fail": 0.0,
            "resonance": 0.0,
            "u_brace": 0.0,
            "current": self._state.current,
        }

    def set_inputs(self, **kwargs) -> None:
        """Update event inputs consumed on subsequent steps (thread-safe)."""
        with self._lock:
            for key, value in kwargs.items():
                if key not in self._inputs:
                    raise KeyError(f"unknown daemon input: {key}")
                self._inputs[key] = float(value)

    def step_once(self, dt: float) -> BiophysicalState:
        """Advance the ODEs by dt seconds; returns a snapshot (thread-safe)."""
        raw_dt = max(dt, 0.0)
        dt = min(raw_dt, self.max_dt_s)
        with self._lock:
            inputs = dict(self._inputs)
            vec = rk4_step(
                [self._state.sigma, self._state.valence, self._state.gamma, self._state.T_coil],
                dt,
                mismatch=inputs["mismatch"],
                u_recovery=inputs["u_recovery"],
                success=inputs["success"],
                fail=inputs["fail"],
                resonance=inputs["resonance"],
                u_brace=inputs["u_brace"],
                current=inputs["current"],
                p=self.params,
            )
            self._state.sigma, self._state.valence, self._state.gamma, self._state.T_coil = (
                float(vec[0]),
                float(vec[1]),
                float(vec[2]),
                float(vec[3]),
            )
            self._state.clamp()
            self._state.current = inputs["current"]
            self._state.mismatch_delta = inputs["mismatch"]
            self._state.rho_tau = (
                raw_dt / self.params.tau_sigma if self.params.tau_sigma > 0 else 0.0
            )
            self._state.timestamp_ns = time.monotonic_ns()
            snapshot = replace(self._state)
            self._history.append(snapshot)
            return snapshot

    def start(self) -> None:
        """Start the background loop; idempotent."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="jamesian-autonomic", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop the background loop; idempotent."""
        thread = None
        with self._lock:
            thread = self._thread
            self._thread = None
        self._stop.set()
        if thread is not None:
            thread.join(timeout=5.0)

    @property
    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def get_state(self) -> BiophysicalState:
        """Latest state snapshot (thread-safe)."""
        with self._lock:
            return replace(self._state)

    def history(self) -> list[BiophysicalState]:
        """Copy of the bounded state history (thread-safe)."""
        with self._lock:
            return list(self._history)

    def _loop(self) -> None:
        period = 1.0 / self.frequency_hz
        last_ns = time.monotonic_ns()
        while not self._stop.is_set():
            time.sleep(period)
            now_ns = time.monotonic_ns()
            self.step_once((now_ns - last_ns) / 1e9)
            last_ns = now_ns
