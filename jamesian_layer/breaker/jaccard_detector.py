"""Rolling Jaccard lexical similarity tracker (spec section 5.4).

Tokenization is lowercase [a-z0-9]+ with a frozen minimal stopword set, so
identical tool-call retries score J = 1.0 while empty or boilerplate-only
turns score J = 0.0 and can never trip the breaker.
"""

import re

STOPWORDS = frozenset(
    """
    a an the and or to of in on at for with as by from into over after
    before not no do does did done will would can could should shall may
    might must is are was were be been being it its this that these those
    i you he she we they my your his her our their me him us them
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    return {t for t in _TOKEN_RE.findall(text.lower())} - STOPWORDS


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


class JaccardDetector:
    """Trips when `window_k` consecutive turns match at J >= threshold.

    Run-length counts turns, not pairs: three identical turns produce scores
    [0.0, 1.0, 1.0] and trip on the third, per spec Test 1. The first
    observed turn seeds the run at length 1.
    """

    def __init__(self, threshold: float = 0.70, window_k: int = 3):
        self.threshold = threshold
        self.window_k = window_k
        self._previous: set[str] | None = None
        self._run = 0

    def observe(self, text: str) -> float:
        tokens = tokenize(text)
        if self._previous is None:
            score = 0.0
            self._run = 1
        else:
            score = jaccard(tokens, self._previous)
            self._run = self._run + 1 if score >= self.threshold else 1
        self._previous = tokens
        return score

    @property
    def tripped(self) -> bool:
        return self._run >= self.window_k

    @property
    def run(self) -> int:
        return self._run

    def reset(self) -> None:
        self._previous = None
        self._run = 0
