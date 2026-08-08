from pathlib import Path

from spacemouse_bridge.device.decoders import (
    RotationReport,
    TranslationReport,
    decode_report,
)
from spacemouse_bridge.device.reader import RawReport, ReplayReader, dump_to_jsonl

FIXTURES = Path(__file__).parent / "fixtures"


def test_replay_reader_reproduces_recorded_reports():
    reader = ReplayReader(FIXTURES / "spacemouse_pro_buttons.jsonl")
    first = reader.read()
    assert first is not None
    assert first.report_id == 0x03
    assert len(first.data) == 6


def test_replay_reader_returns_none_when_exhausted():
    reader = ReplayReader(FIXTURES / "spacemouse_pro_buttons.jsonl")
    count = 0
    while reader.read() is not None:
        count += 1
    assert count == 30  # captured in docs/protocol.md
    assert reader.read() is None


def test_axis_tx_fixture_is_dominated_by_tx():
    # Real capture: user pushed strictly left-right (docs/protocol.md).
    reader = ReplayReader(FIXTURES / "spacemouse_pro_axis_tx.jsonl")
    max_abs_tx = 0
    max_abs_other = 0
    report = reader.read()
    while report is not None:
        decoded = decode_report(report.report_id, report.data)
        if isinstance(decoded, TranslationReport):
            max_abs_tx = max(max_abs_tx, abs(decoded.tx))
            max_abs_other = max(max_abs_other, abs(decoded.ty), abs(decoded.tz))
        elif isinstance(decoded, RotationReport):
            max_abs_other = max(
                max_abs_other, abs(decoded.rx), abs(decoded.ry), abs(decoded.rz)
            )
        report = reader.read()

    assert max_abs_tx > 300
    assert max_abs_other < max_abs_tx


class _FakeReader:
    def __init__(self, reports: list[RawReport]):
        self._reports = list(reports)

    def read(self, timeout_ms: int = 100):
        return self._reports.pop(0) if self._reports else None

    def close(self) -> None:
        pass


def test_dump_to_jsonl_writes_all_available_reports(tmp_path):
    reports = [
        RawReport(t=0.0, report_id=1, data=b"\x01\x00\x00\x00\x00\x00"),
        RawReport(t=0.01, report_id=2, data=b"\x00\x00\x00\x00\x00\x00"),
    ]
    fake = _FakeReader(reports)
    out_path = tmp_path / "out.jsonl"

    count = dump_to_jsonl(fake, out_path, duration_s=0.05)

    assert count == 2
    replayed = ReplayReader(out_path)
    first = replayed.read()
    second = replayed.read()
    assert first.report_id == 1
    assert second.report_id == 2
    assert replayed.read() is None
