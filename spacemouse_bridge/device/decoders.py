"""Parse raw HID report bodies into typed axis/button reports.

Format is documented in docs/protocol.md, captured from a real SpaceMouse
Pro (Фаза 0 разведка, docs/PLAN.md §5). This is the "old generation" layout:
translation and rotation arrive as two separate 6-byte reports rather than
one combined report, and there is no periodic zero/heartbeat report -- the
device stays silent while at rest. Combining partial reports into a full
6DoF state is core/state.py's job (§6.2 задача 4), not this module's.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

REPORT_ID_TRANSLATION = 0x01
REPORT_ID_ROTATION = 0x02
REPORT_ID_BUTTONS = 0x03

_AXIS_TRIPLE = struct.Struct("<3h")
_AXIS_SEXTUPLE = struct.Struct("<6h")


@dataclass(frozen=True)
class TranslationReport:
    tx: int
    ty: int
    tz: int


@dataclass(frozen=True)
class RotationReport:
    rx: int
    ry: int
    rz: int


@dataclass(frozen=True)
class CombinedAxisReport:
    """New-generation devices: all six axes in one report."""

    tx: int
    ty: int
    tz: int
    rx: int
    ry: int
    rz: int


@dataclass(frozen=True)
class ButtonReport:
    buttons: int
    """Bitmask, one bit per physical button (uint48, byte order as sent)."""


DecodedReport = TranslationReport | RotationReport | CombinedAxisReport | ButtonReport


def decode_report(report_id: int, data: bytes) -> DecodedReport | None:
    """Decode one raw report body. Returns None for unknown/short reports.

    Report length decides old- vs new-generation layout, not the device
    model -- see docs/PLAN.md §3.1.
    """
    if report_id == REPORT_ID_TRANSLATION:
        if len(data) >= 12:
            tx, ty, tz, rx, ry, rz = _AXIS_SEXTUPLE.unpack_from(data)
            return CombinedAxisReport(tx, ty, tz, rx, ry, rz)
        if len(data) >= 6:
            tx, ty, tz = _AXIS_TRIPLE.unpack_from(data)
            return TranslationReport(tx, ty, tz)
        return None

    if report_id == REPORT_ID_ROTATION:
        if len(data) >= 6:
            rx, ry, rz = _AXIS_TRIPLE.unpack_from(data)
            return RotationReport(rx, ry, rz)
        return None

    if report_id == REPORT_ID_BUTTONS:
        if not data:
            return None
        return ButtonReport(int.from_bytes(data, "little"))

    return None
