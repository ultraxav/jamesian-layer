"""Rolling 10-cycle lexical refractory ban-list (spec section 5.4)."""

from collections import Counter, deque

from jamesian_layer.breaker.jaccard_detector import STOPWORDS, tokenize


class TabooBuffer:
    def __init__(self, max_cycles: int = 10, top_n: int = 4):
        self.max_cycles = max_cycles
        self.top_n = top_n
        self._cycles: deque[frozenset[str]] = deque(maxlen=max_cycles)

    def add_from_turn(self, text: str) -> frozenset[str]:
        # Sorted input keeps most_common ties alphabetical (deterministic);
        # pure digits are telemetry noise, never taboo candidates.
        counts = Counter(
            t for t in sorted(tokenize(text)) if t not in STOPWORDS and not t.isdigit()
        )
        kept = frozenset(word for word, _ in counts.most_common(self.top_n))
        if kept:
            self._cycles.append(kept)
        return kept

    def active(self) -> list[str]:
        return sorted({word for cycle in self._cycles for word in cycle})

    def directive(self) -> str | None:
        words = self.active()
        if not words:
            return None
        return f"[CIRCUIT_BREAKER_ACTIVE: TABOO_WORDS = {words!r}]"

    def __len__(self) -> int:
        return len(self._cycles)

    def clear(self) -> None:
        self._cycles.clear()
