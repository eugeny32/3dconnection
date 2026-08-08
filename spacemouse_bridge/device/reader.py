"""Read raw HID reports from a SpaceMouse, or replay a captured dump.

HidReader and ReplayReader implement the same Reader protocol so the rest
of the pipeline (and tests) never need to know whether they're driven by
real hardware or a JSONL fixture (docs/PLAN.md §6.3).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import hid


@dataclass(frozen=True)
class RawReport:
    t: float
    """Seconds since the reader was opened."""
    report_id: int
    data: bytes
    """Report body, with the leading report-id byte already stripped."""


class Reader(Protocol):
    def read(self, timeout_ms: int = 100) -> RawReport | None: ...
    def close(self) -> None: ...


class HidReader:
    """Reads raw reports from a real SpaceMouse over hidapi."""

    def __init__(self, vendor_id: int, product_id: int, report_size: int = 64):
        self._dev = hid.Device(vid=vendor_id, pid=product_id)
        self._report_size = report_size
        self._t0 = time.monotonic()

    def read(self, timeout_ms: int = 100) -> RawReport | None:
        raw = self._dev.read(self._report_size, timeout=timeout_ms)
        if not raw:
            return None
        return RawReport(
            t=time.monotonic() - self._t0,
            report_id=raw[0],
            data=bytes(raw[1:]),
        )

    def close(self) -> None:
        self._dev.close()

    def __enter__(self) -> "HidReader":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class ReplayReader:
    """Replays a JSONL dump captured via `--dump`, for tests without hardware."""

    def __init__(self, path: Path | str):
        self._records: list[RawReport] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self._records.append(
                    RawReport(
                        t=obj["t"],
                        report_id=obj["report_id"],
                        data=bytes(obj["data"]),
                    )
                )
        self._index = 0

    def read(self, timeout_ms: int = 100) -> RawReport | None:
        if self._index >= len(self._records):
            return None
        record = self._records[self._index]
        self._index += 1
        return record

    def close(self) -> None:
        pass

    def __enter__(self) -> "ReplayReader":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def dump_to_jsonl(reader: Reader, out_path: Path | str, duration_s: float) -> int:
    """Read from `reader` for `duration_s` seconds, writing each report as JSONL.

    Returns the number of reports written. Used by both `--dump` and the
    manual fixture-capture scripts described in docs/protocol.md.
    """
    count = 0
    deadline = time.monotonic() + duration_s
    with open(out_path, "w", encoding="utf-8") as f:
        while time.monotonic() < deadline:
            report = reader.read(timeout_ms=100)
            if report is None:
                continue
            f.write(
                json.dumps(
                    {
                        "t": round(report.t, 4),
                        "report_id": report.report_id,
                        "data": list(report.data),
                    }
                )
                + "\n"
            )
            count += 1
    return count
