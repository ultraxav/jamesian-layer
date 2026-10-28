"""KV-cache invariant telemetry injection (suffix-only, prefix-preserving)."""

from jamesian_layer.kv_cache.prefix_verifier import prefix_hash, verify_suffix_only
from jamesian_layer.kv_cache.suffix_formatter import (
    TELEMETRY_PATTERN,
    check_token_budget,
    estimate_tokens,
    format_suffix,
    parse_telemetry,
    telemetry_comment,
)

__all__ = [
    "TELEMETRY_PATTERN",
    "check_token_budget",
    "estimate_tokens",
    "format_suffix",
    "parse_telemetry",
    "prefix_hash",
    "telemetry_comment",
    "verify_suffix_only",
]
