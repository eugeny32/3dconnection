from spacemouse_bridge.core.state import AxisState, StateAccumulator
from spacemouse_bridge.device.decoders import (
    ButtonReport,
    CombinedAxisReport,
    RotationReport,
    TranslationReport,
)


def test_initial_state_is_all_zero():
    acc = StateAccumulator()
    assert acc.read(t=0.0) == AxisState(t=0.0)


def test_translation_update_leaves_rotation_untouched():
    acc = StateAccumulator()
    acc.update(TranslationReport(tx=100, ty=-50, tz=0), t=0.0)
    acc.update(RotationReport(rx=10, ry=0, rz=-10), t=0.01)

    state = acc.read(t=0.02)

    assert (state.tx, state.ty, state.tz) == (100, -50, 0)
    assert (state.rx, state.ry, state.rz) == (10, 0, -10)


def test_combined_report_updates_both_groups_at_once():
    acc = StateAccumulator()
    acc.update(CombinedAxisReport(tx=1, ty=2, tz=3, rx=4, ry=5, rz=6), t=0.0)

    state = acc.read(t=0.0)

    assert (state.tx, state.ty, state.tz, state.rx, state.ry, state.rz) == (
        1, 2, 3, 4, 5, 6,
    )


def test_button_report_updates_bitmask_without_touching_axes():
    acc = StateAccumulator()
    acc.update(TranslationReport(tx=50, ty=0, tz=0), t=0.0)
    acc.update(ButtonReport(buttons=0b101), t=0.0)

    state = acc.read(t=0.0)

    assert state.buttons == 0b101
    assert state.tx == 50


def test_group_zeroes_out_after_release_timeout():
    acc = StateAccumulator(release_timeout_s=0.1)
    acc.update(TranslationReport(tx=200, ty=0, tz=0), t=0.0)

    still_active = acc.read(t=0.05)
    assert still_active.tx == 200

    released = acc.read(t=0.2)
    assert released.tx == 0


def test_translation_and_rotation_release_independently():
    acc = StateAccumulator(release_timeout_s=0.1)
    acc.update(TranslationReport(tx=200, ty=0, tz=0), t=0.0)
    acc.update(RotationReport(rx=0, ry=0, rz=0), t=0.15)

    state = acc.read(t=0.2)

    assert state.tx == 0  # translation stale (last update at t=0.0)
    assert state.rz == 0  # rotation fresh (last update at t=0.15)
