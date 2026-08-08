import io
import re
from pathlib import Path

from spacemouse_bridge.app.viz import AXIS_LABELS, render_bar, render_frame, run_viz
from spacemouse_bridge.core.state import AxisState
from spacemouse_bridge.device.reader import ReplayReader

FIXTURES = Path(__file__).parent / "fixtures"

VALUE_RE = re.compile(r"\] *(-?\d+)$")


def _value_of(bar_line: str) -> int:
    match = VALUE_RE.search(bar_line)
    assert match, bar_line
    return int(match.group(1))


def test_render_bar_zero_is_centered_empty():
    bar = render_bar(0)
    assert _value_of(bar) == 0
    assert "#" not in bar


def test_render_bar_positive_fills_right_of_center():
    bar = render_bar(350, axis_range=350)
    inside = bar[1 : bar.index("]")]
    center = len(inside) // 2
    assert "#" in inside[center:]
    assert "#" not in inside[:center]


def test_render_bar_negative_fills_left_of_center():
    bar = render_bar(-350, axis_range=350)
    inside = bar[1 : bar.index("]")]
    center = len(inside) // 2
    assert "#" in inside[:center]
    assert "#" not in inside[center:]


def test_render_bar_clamps_beyond_range():
    assert render_bar(10_000, axis_range=350) == render_bar(350, axis_range=350).replace(
        "  350", "10000"
    )


def test_render_frame_has_one_line_per_axis_in_order():
    state = AxisState(tx=1, ty=2, tz=3, rx=4, ry=5, rz=6)
    lines = render_frame(state).splitlines()
    assert len(lines) == len(AXIS_LABELS)
    for label, line in zip(AXIS_LABELS, lines):
        assert line.strip().startswith(label)


class _FakeClock:
    """Advances by `step` seconds every time it's called (deterministic tests)."""

    def __init__(self, step: float = 1 / 240):
        self.t = 0.0
        self.step = step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


class _NullReader:
    def read(self, timeout_ms: int = 100):
        return None

    def close(self) -> None:
        pass


def test_run_viz_prints_all_zero_frames_when_idle():
    out = io.StringIO()
    run_viz(_NullReader(), hz=60.0, stdout=out, clock=_FakeClock(), max_frames=3)

    text = out.getvalue()
    frames = [f for f in text.split("\x1b[") if f]
    # Strip the leading "<N>A" cursor-up prefix from repaint frames.
    cleaned = [re.sub(r"^\d+A", "", f) for f in frames]
    assert len(cleaned) == 3
    for frame in cleaned:
        for line in frame.strip("\n").splitlines():
            assert _value_of(line) == 0


def test_run_viz_repaints_in_place_after_first_frame():
    out = io.StringIO()
    run_viz(_NullReader(), hz=60.0, stdout=out, clock=_FakeClock(), max_frames=3)

    text = out.getvalue()
    assert text.count("\x1b[") == 2  # frames 2 and 3 move the cursor up; frame 1 doesn't


def test_run_viz_shows_nonzero_axis_while_replaying_real_capture():
    reader = ReplayReader(FIXTURES / "spacemouse_pro_axis_tx.jsonl")
    out = io.StringIO()

    # Every iteration with a report advances the fake clock by 3 * step (vs
    # 2 * step when idle), so draining all 815 records alone takes ~611
    # frames; give it enough headroom to drain fully and clear the release
    # timeout afterwards.
    run_viz(reader, hz=60.0, stdout=out, clock=_FakeClock(), max_frames=700)

    raw_blocks = out.getvalue().split("\x1b[")
    frames = [raw_blocks[0]] + [re.sub(r"^\d+A", "", b) for b in raw_blocks[1:]]

    tx_values = []
    for frame in frames:
        for line in frame.splitlines():
            if line.strip().startswith("tx"):
                tx_values.append(_value_of(line))

    assert any(abs(v) > 300 for v in tx_values)
    assert tx_values[-1] == 0  # fully released well before max_frames is reached
