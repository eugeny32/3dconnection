"""Combine partial translation/rotation/button reports into one 6DoF state.

The device sends translation and rotation as separate reports and stays
completely silent while at rest -- there is no "back to zero" report
(docs/protocol.md). StateAccumulator therefore tracks *when* each group was
last updated and zeroes it out once `release_timeout_s` has passed, instead
of latching the last nonzero value forever.
"""

from __future__ import annotations

from dataclasses import dataclass

from spacemouse_bridge.device.decoders import (
    ButtonReport,
    CombinedAxisReport,
    DecodedReport,
    RotationReport,
    TranslationReport,
)

DEFAULT_RELEASE_TIMEOUT_S = 0.3
"""Reports arrive every ~15ms while active (docs/protocol.md); comfortably
longer than any single gap, short enough that a released axis snaps back
to zero without a perceptible stall."""


@dataclass(frozen=True)
class AxisState:
    tx: int = 0
    ty: int = 0
    tz: int = 0
    rx: int = 0
    ry: int = 0
    rz: int = 0
    buttons: int = 0
    t: float = 0.0


class StateAccumulator:
    def __init__(self, release_timeout_s: float = DEFAULT_RELEASE_TIMEOUT_S):
        self._release_timeout_s = release_timeout_s
        self._translation = (0, 0, 0)
        self._rotation = (0, 0, 0)
        self._buttons = 0
        self._last_translation_t: float | None = None
        self._last_rotation_t: float | None = None

    def update(self, report: DecodedReport, t: float) -> None:
        if isinstance(report, CombinedAxisReport):
            self._translation = (report.tx, report.ty, report.tz)
            self._rotation = (report.rx, report.ry, report.rz)
            self._last_translation_t = t
            self._last_rotation_t = t
        elif isinstance(report, TranslationReport):
            self._translation = (report.tx, report.ty, report.tz)
            self._last_translation_t = t
        elif isinstance(report, RotationReport):
            self._rotation = (report.rx, report.ry, report.rz)
            self._last_rotation_t = t
        elif isinstance(report, ButtonReport):
            self._buttons = report.buttons

    def read(self, t: float) -> AxisState:
        tx, ty, tz = self._translation
        if self._is_stale(self._last_translation_t, t):
            tx, ty, tz = 0, 0, 0

        rx, ry, rz = self._rotation
        if self._is_stale(self._last_rotation_t, t):
            rx, ry, rz = 0, 0, 0

        return AxisState(
            tx=tx, ty=ty, tz=tz, rx=rx, ry=ry, rz=rz, buttons=self._buttons, t=t
        )

    def _is_stale(self, last_update_t: float | None, now: float) -> bool:
        return last_update_t is None or (now - last_update_t) > self._release_timeout_s
