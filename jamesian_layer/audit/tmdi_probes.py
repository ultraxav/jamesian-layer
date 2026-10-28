"""Calibrated chronometric lag probes (spec section 5.7).

TMDI shifts afferent feedback timestamps by Δt. Tests use virtual
timestamps; live sweeps additionally sleep for real time.
"""

import asyncio

LEVELS = (0.25, 0.5, 1.0, 2.0)


class ChronometricLag:
    def __init__(self, seconds: float):
        if seconds < 0.0:
            raise ValueError(f"lag must be non-negative: {seconds}")
        self.seconds = seconds

    def apply(self, timestamp_ns: int) -> int:
        return timestamp_ns + int(self.seconds * 1e9)

    async def live_delay(self) -> None:
        await asyncio.sleep(self.seconds)


def ladder() -> list[ChronometricLag]:
    return [ChronometricLag(seconds) for seconds in LEVELS]
