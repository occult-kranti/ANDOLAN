"""Offline event-window inspection adapted from Source 2 Viewer, not combat.

MIT attribution and exact upstream source: ../NOTICE.md. No game data is used.
The upstream whole-timeline rule yields each authored event once even when an
update spans several loops. This inspector preserves that visual-inspection
rule; it must never be used to infer projectile/damage or repeated audio counts.
"""

from __future__ import annotations

import math


def sampled_indices(cycles: list[float], duration: float, previous: float,
                    current: float, *, finished: bool = False) -> list[int]:
    """Return indices crossing the VRF half-open playback window.

    Admission guards are local additions. Exact non-loop terminal updates are
    closed, pauses/restarts emit nothing, and ordinary wrapped windows are
    half-open. Input events stay in source order, including equal-time events.
    """
    if type(finished) is not bool or not isinstance(cycles, list):
        raise ValueError("invalid timeline container/finished type")
    scalars = [duration, previous, current, *cycles]
    if any(type(value) not in (int, float) or not math.isfinite(value)
           for value in scalars):
        raise ValueError("timeline values must be finite numbers")
    if duration < 0 or previous < 0 or current < 0:
        raise ValueError("negative timeline")
    if any(cycle < 0 or cycle > 1 for cycle in cycles):
        raise ValueError("event outside normalized clip")
    if duration == 0 or current <= previous:
        return []
    if finished and (current != duration or previous >= duration):
        raise ValueError("finished requires the final non-loop window")
    def to_cycles(time: float) -> float:
        cycle = time / duration
        if not math.isfinite(cycle):
            raise ValueError("normalized playback clock overflow")
        # Local correction: 3 * .4 / .4 is 3.0000000000000004 in Python.
        # Recognize exactly represented duration multiples; use no time epsilon.
        nearest = round(cycle)
        return float(nearest) if time == nearest * duration else cycle

    start = to_cycles(previous)
    end = to_cycles(current)
    whole = end - start >= 1
    start -= math.floor(start)
    end -= math.floor(end)

    def fires(cycle: float) -> bool:
        if whole:
            return True
        if finished and cycle >= start:
            return True
        if start <= end:
            return cycle >= start and cycle < end
        return cycle >= start or cycle < end

    return [index for index, cycle in enumerate(cycles) if fires(cycle)]
