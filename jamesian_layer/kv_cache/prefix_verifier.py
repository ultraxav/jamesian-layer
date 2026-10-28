"""Prefix-invariance audit: prove suffix injection left history untouched."""

import hashlib


def prefix_hash(text: str) -> str:
    """SHA-256 hex digest of a prompt prefix (turns 0..T-1)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_suffix_only(before: str, after: str) -> str:
    """Assert `after` is exactly `before` plus an appended suffix.

    Returns the suffix. Raises ValueError when any prefix byte changed.
    """
    if not after.startswith(before):
        raise ValueError("prefix bytes changed: suffix injection is not suffix-only")
    return after[len(before):]
