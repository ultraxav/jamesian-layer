"""Chronometric efferent-afferent lag tracker (spec section 5.3)."""

from collections import OrderedDict


class LagTracker:
    """Registry of dispatch timestamps keyed by action_id.

    Unknown action_ids on feedback raise KeyError: unmatched afferents are a
    wiring bug, never silently scored as nominal.
    """

    def __init__(self, lag_threshold_ms: float = 200.0, max_entries: int = 1024):
        self.lag_threshold_ms = lag_threshold_ms
        self.max_entries = max_entries
        self._pending: OrderedDict[str, int] = OrderedDict()

    def note_efference(self, action_id: str, timestamp_ns: int) -> None:
        self._pending[action_id] = timestamp_ns
        self._pending.move_to_end(action_id)
        while len(self._pending) > self.max_entries:
            self._pending.popitem(last=False)

    def note_afferent(self, action_id: str, timestamp_ns: int) -> float:
        try:
            sent_ns = self._pending.pop(action_id)
        except KeyError:
            raise KeyError(f"afferent for unknown action_id: {action_id!r}")
        return max(0.0, (timestamp_ns - sent_ns) / 1e6)

    def is_lagging(self, lag_ms: float) -> bool:
        return lag_ms > self.lag_threshold_ms

    def __len__(self) -> int:
        return len(self._pending)
