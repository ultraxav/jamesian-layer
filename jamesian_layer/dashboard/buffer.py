"""Thread-safe bounded telemetry ring buffer (spec section 6, step 5)."""

import threading
from collections import deque

from jamesian_layer.core.biophysical_state import BiophysicalState


class TelemetryBuffer:
    """Bounded history of somatic snapshots; drops oldest silently when full."""

    def __init__(self, maxlen: int = 300):
        self._samples: deque[dict] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def append(self, state: BiophysicalState) -> None:
        with self._lock:
            self._samples.append(state.to_telemetry_dict())

    def snapshot(self, n: int | None = None) -> list[dict]:
        """Newest-n telemetry dicts, oldest-first."""
        with self._lock:
            items = list(self._samples)
        return items[-n:] if n is not None else items

    def latest(self) -> dict | None:
        with self._lock:
            return self._samples[-1] if self._samples else None

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples)
