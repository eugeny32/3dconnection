"""Live 6-axis terminal visualization (Фаза 1, docs/PLAN.md §5).

Reads raw reports as fast as the device offers them, decodes and folds them
into an AxisState via StateAccumulator, and repaints six bars at a fixed
tick rate (default 60Hz) -- decoupling repaint rate from report rate is
what keeps the bars reading as smooth motion instead of jittering with
every ~15ms report.
"""

from __future__ import annotations

import sys
import time
from typing import IO, Callable

from spacemouse_bridge.core.state import AxisState, StateAccumulator
from spacemouse_bridge.device.decoders import decode_report
from spacemouse_bridge.device.reader import Reader

AXIS_LABELS = ("tx", "ty", "tz", "rx", "ry", "rz")
DEFAULT_AXIS_RANGE = 350.0
DEFAULT_BAR_WIDTH = 20


def render_bar(
    value: int, axis_range: float = DEFAULT_AXIS_RANGE, width: int = DEFAULT_BAR_WIDTH
) -> str:
    """One bar: centered zero point, fills outward, exact value trails it."""
    ratio = max(-1.0, min(1.0, value / axis_range)) if axis_range else 0.0
    center = width // 2
    filled = round(abs(ratio) * center)
    cells = [" "] * width
    cells[center] = "|"
    if ratio > 0:
        for i in range(filled):
            cells[min(width - 1, center + 1 + i)] = "#"
    elif ratio < 0:
        for i in range(filled):
            cells[max(0, center - 1 - i)] = "#"
    return "[" + "".join(cells) + f"] {value:5d}"


def render_frame(state: AxisState) -> str:
    return "\n".join(
        f"{label:>2} {render_bar(getattr(state, label))}" for label in AXIS_LABELS
    )


def run_viz(
    reader: Reader,
    *,
    hz: float = 60.0,
    release_timeout_s: float = 0.3,
    stdout: IO[str] = sys.stdout,
    clock: Callable[[], float] = time.monotonic,
    max_frames: int | None = None,
) -> None:
    """Drive the visualization loop until interrupted or max_frames is hit.

    max_frames exists purely for tests -- real usage runs until Ctrl+C.
    """
    accumulator = StateAccumulator(release_timeout_s=release_timeout_s)
    frame_interval = 1.0 / hz
    t0 = clock()
    next_frame_t = t0
    frame_count = 0
    printed_lines = 0

    try:
        while max_frames is None or frame_count < max_frames:
            now = clock()
            remaining_ms = max(1, round((next_frame_t - now) * 1000))
            report = reader.read(timeout_ms=min(remaining_ms, 100))
            if report is not None:
                decoded = decode_report(report.report_id, report.data)
                if decoded is not None:
                    accumulator.update(decoded, t=clock() - t0)

            now = clock()
            if now < next_frame_t:
                continue

            state = accumulator.read(t=now - t0)
            frame = render_frame(state)
            if printed_lines:
                stdout.write(f"\x1b[{printed_lines}A")
            stdout.write(frame + "\n")
            stdout.flush()
            printed_lines = frame.count("\n") + 1
            frame_count += 1

            next_frame_t += frame_interval
            if next_frame_t < now:
                next_frame_t = now + frame_interval
    except KeyboardInterrupt:
        pass
