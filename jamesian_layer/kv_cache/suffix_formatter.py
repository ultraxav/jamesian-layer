"""Suffix-only telemetry formatter (spec section 5.2).

The formatter only ever appends to the tail of a tool response: it never
reads, reorders, or rewrites preceding turns, which is what preserves the
KV-cache prefix. Token accounting uses a conservative character-based
upper bound until the Llama 3 tokenizer check lands (Phase 3).
"""

import math
import re

from jamesian_layer.core.biophysical_state import BiophysicalState

TELEMETRY_PATTERN = re.compile(
    r"<!-- SOMATIC_TELEMETRY:\s*σ=([0-9.]+)\s*\|\s*V=([+-][0-9.]+)\s*\|\s*"
    r"γ=([0-9.]+)\s*\|\s*T_coil=([0-9.]+)C\s*\|\s*ρ_τ=([0-9.]+)\s*\|\s*"
    r"EfferenceΔ=([0-9.]+) -->"
)

TOKEN_BUDGET = 45
CHARS_PER_TOKEN = 4


def telemetry_comment(state: BiophysicalState) -> str:
    """Render the single-line somatic telemetry comment for a state."""
    t = state.to_telemetry_dict()
    valence = f"{t['valence']:+.2f}"
    return (
        f"<!-- SOMATIC_TELEMETRY: σ={t['sigma']:.2f} | V={valence} | "
        f"γ={t['gamma']:.2f} | T_coil={t['T_coil']:.1f}C | "
        f"ρ_τ={t['rho_tau']:.2f} | EfferenceΔ={t['mismatch_delta']:.2f} -->"
    )


def format_exteroceptive_result(
    *,
    cmd_velocity: float = 0.0,
    velocity: float = 0.0,
    displacement: float = 0.0,
) -> str:
    """Render the arm-neutral exteroceptive odometry line shared by Vanilla and Jamesian."""
    return (
        f"[TOOL_RESULT: cmd_v={cmd_velocity:.1f}m/s | "
        f"actual_v={velocity:.1f}m/s | dx={displacement:.1f}m]"
    )


def format_suffix(
    state: BiophysicalState,
    *,
    status: str = "SUCCESS",
    code: int = 0,
    displacement: float = 0.0,
    velocity: float = 0.0,
    cmd_velocity: float | None = None,
) -> str:
    """Build the two-line tail suffix: status line plus telemetry comment."""
    if cmd_velocity is not None:
        first = format_exteroceptive_result(
            cmd_velocity=cmd_velocity,
            velocity=velocity,
            displacement=displacement,
        )
    elif status == "BLOCKED":
        first = f"[TOOL_RESULT: BLOCKED | displacement={displacement:.1f}m | velocity={velocity:.1f}m/s]"
    else:
        first = f"[TOOL_RESULT: {status} | code={code}]"
    return f"{first}\n{telemetry_comment(state)}"


def parse_telemetry(comment: str) -> dict:
    """Extract the six telemetry fields; raises ValueError when absent."""
    match = TELEMETRY_PATTERN.search(comment)
    if match is None:
        raise ValueError("no SOMATIC_TELEMETRY block found")
    keys = ("sigma", "valence", "gamma", "T_coil", "rho_tau", "mismatch_delta")
    return {key: float(value) for key, value in zip(keys, match.groups())}


def estimate_tokens(text: str) -> int:
    """Conservative token upper bound (chars/4, rounded up)."""
    return max(1, math.ceil(len(text) / CHARS_PER_TOKEN))


def check_token_budget(state: BiophysicalState, **kwargs) -> tuple[int, bool]:
    """Returns (estimated_tokens, within_budget) for the full suffix."""
    estimate = estimate_tokens(format_suffix(state, **kwargs))
    return estimate, estimate <= TOKEN_BUDGET
