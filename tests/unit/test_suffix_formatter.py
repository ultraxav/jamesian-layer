"""Unit tests for the suffix formatter and prefix verifier (gate, spec 7.2)."""

import pytest

from jamesian_layer.kv_cache.prefix_verifier import prefix_hash, verify_suffix_only
from jamesian_layer.kv_cache.suffix_formatter import (
    TOKEN_BUDGET,
    check_token_budget,
    estimate_tokens,
    format_suffix,
    parse_telemetry,
)


def test_suffix_appends_only(state):
    from jamesian_layer.kv_cache.suffix_formatter import telemetry_comment

    before = "[TOOL_RESULT: SUCCESS | code=0]"
    comment = telemetry_comment(state)
    after = before + "\n" + comment
    assert verify_suffix_only(before, after) == "\n" + comment


def test_prefix_bytes_identical(state):
    before = "turn0 tool call\nturn1 tool result ok"
    suffix = format_suffix(state)
    after = before + suffix
    assert after[: len(before)] == before
    assert prefix_hash(after[: len(before)]) == prefix_hash(before)


def test_regex_round_trip(state):
    state.sigma = 0.22
    state.valence = 0.35
    state.T_coil = 28.1
    from jamesian_layer.kv_cache.suffix_formatter import telemetry_comment

    fields = parse_telemetry(telemetry_comment(state))
    expected = state.to_telemetry_dict()
    for key, value in expected.items():
        assert fields[key] == pytest.approx(value)


def test_token_budget(state):
    estimate, ok = check_token_budget(state)
    assert ok
    assert estimate <= TOKEN_BUDGET
    assert estimate_tokens(format_suffix(state)) <= TOKEN_BUDGET


def test_blocked_variant(state):
    suffix = format_suffix(state, status="BLOCKED", displacement=0.0, velocity=0.0)
    assert suffix.startswith("[TOOL_RESULT: BLOCKED | displacement=0.0m")
    comment = suffix.split("\n", 1)[1]
    assert parse_telemetry(comment)["mismatch_delta"] == pytest.approx(
        state.to_telemetry_dict()["mismatch_delta"]
    )


def test_verifier_rejects_prefix_mutation():
    with pytest.raises(ValueError):
        verify_suffix_only("abc", "aXc suffix")
