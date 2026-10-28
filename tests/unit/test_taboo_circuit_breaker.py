"""Unit tests for the Jaccard taboo circuit-breaker (gate, spec 7.2)."""

from jamesian_layer.breaker.jaccard_detector import JaccardDetector, jaccard, tokenize
from jamesian_layer.breaker.taboo_buffer import TabooBuffer

DRIVE = "robot_actuator velocity 1.0 heading 0.0 drive forward"
TURN = "turn_bearing angle 90 turn left"


def test_trips_at_third_identical_cycle():
    det = JaccardDetector()
    assert det.observe(DRIVE) == 0.0  # first turn has no predecessor
    assert det.observe(DRIVE) == 1.0
    assert det.tripped is False
    assert det.observe(DRIVE) == 1.0
    assert det.tripped is True
    assert det.run == 3


def test_varied_commands_never_trip():
    det = JaccardDetector()
    for text in [DRIVE, TURN, "cool_down rest vent heat", "heartbeat_ping status check"]:
        det.observe(text)
    assert det.tripped is False


def test_streak_resets_on_divergence():
    det = JaccardDetector()
    det.observe(DRIVE)
    det.observe(DRIVE)
    det.observe(TURN)
    assert det.run == 1
    assert det.tripped is False


def test_empty_turns_never_trip():
    assert jaccard(set(), set()) == 0.0
    det = JaccardDetector()
    for _ in range(5):
        det.observe("the and to of")
    assert det.tripped is False


def test_tokenize_drops_stopwords_keeps_verbs():
    tokens = tokenize("drive the rover forward to the goal")
    assert "the" not in tokens and "to" not in tokens
    assert {"drive", "forward"} <= tokens


def test_taboo_directive_format():
    buf = TabooBuffer()
    buf.add_from_turn(DRIVE)
    directive = buf.directive()
    assert directive is not None
    assert directive.startswith("[CIRCUIT_BREAKER_ACTIVE: TABOO_WORDS = [")
    for word in ("drive", "forward"):
        assert f"'{word}'" in directive


def test_taboo_decays_after_ten_cycles():
    buf = TabooBuffer(max_cycles=10)
    buf.add_from_turn(DRIVE)
    assert "drive" in buf.active()
    for i in range(10):
        buf.add_from_turn(f"unrelated maneuver number {i} alpha beta gamma")
    # The DRIVE entry aged out of the 10-cycle window; later turns remain.
    assert "drive" not in buf.active()
    assert "forward" not in buf.active()
    assert buf.directive() is not None


def test_stopwords_never_tabooed():
    buf = TabooBuffer()
    buf.add_from_turn("the and to of in on")
    assert buf.directive() is None
    assert buf.active() == []
