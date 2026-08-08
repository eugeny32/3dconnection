"""Turn raw per-axis integers into filtered, normalized floats.

Pipeline per docs/PLAN.md §3.3: zero-offset subtraction, radial deadzone,
normalize to [-1, 1], expo curve, dominant-axis suppression, EMA smoothing.

One deliberate deviation from the plan's numbered list: deadzone is applied
*after* normalization rather than before. Profile TOMLs express `deadzone`
as a fraction of full range (e.g. `0.08`, see docs/PLAN.md §3.6) — applying
it in raw-int units would make that number meaningless without also knowing
axis_range. Applying it post-normalize keeps deadzone config unit-agnostic.
"""

from __future__ import annotations

import math

Vector = tuple[float, ...]


def subtract_offset(values: Vector, offset: Vector) -> Vector:
    return tuple(v - o for v, o in zip(values, offset))


def normalize(values: Vector, axis_range: float) -> Vector:
    return tuple(max(-1.0, min(1.0, v / axis_range)) for v in values)


def radial_deadzone(values: Vector, deadzone: float) -> Vector:
    """Deadzone based on vector magnitude, not per-component.

    Per-component deadzone makes diagonal gestures "stick" to one axis near
    the center (docs/PLAN.md §3.3) -- e.g. a shallow diagonal push would
    read as pure-X because Y individually never clears its own threshold.
    """
    if deadzone <= 0:
        return values
    magnitude = math.sqrt(sum(v * v for v in values))
    if magnitude <= deadzone:
        return tuple(0.0 for _ in values)
    scale = min(1.0, (magnitude - deadzone) / (1.0 - deadzone))
    ratio = scale / magnitude
    return tuple(v * ratio for v in values)


def expo_curve(values: Vector, gamma: float) -> Vector:
    """out = sign(x) * |x|^gamma -- more precision near center (gamma > 1)."""
    return tuple(math.copysign(abs(v) ** gamma, v) if v != 0 else 0.0 for v in values)


def dominant_axis_suppress(values: Vector, ratio: float) -> Vector:
    """Zero out axes weaker than the strongest by more than `ratio`.

    ratio <= 0 disables this step (plan's `dominant_axis_ratio = 0` means
    "off"). Prevents orbit from drifting into pan on a slightly-off-axis
    gesture (docs/PLAN.md §3.3).
    """
    if ratio <= 0 or not values:
        return values
    max_abs = max(abs(v) for v in values)
    if max_abs == 0:
        return values
    threshold = max_abs / ratio
    return tuple(v if abs(v) >= threshold else 0.0 for v in values)


class EmaSmoother:
    """Exponential moving average, one running value per vector component."""

    def __init__(self, alpha: float, size: int):
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        self._alpha = alpha
        self._state = [0.0] * size

    def apply(self, values: Vector) -> Vector:
        self._state = [
            self._alpha * v + (1 - self._alpha) * s
            for v, s in zip(values, self._state)
        ]
        return tuple(self._state)

    def reset(self) -> None:
        self._state = [0.0] * len(self._state)
