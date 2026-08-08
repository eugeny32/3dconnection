import math

import pytest

from spacemouse_bridge.core.filters import (
    EmaSmoother,
    dominant_axis_suppress,
    expo_curve,
    normalize,
    radial_deadzone,
    subtract_offset,
)


def test_subtract_offset():
    assert subtract_offset((110.0, 90.0), (10.0, 10.0)) == (100.0, 80.0)


def test_normalize_clamps_to_unit_range():
    assert normalize((350.0, -350.0, 700.0, -700.0), axis_range=350.0) == (
        1.0, -1.0, 1.0, -1.0,
    )


def test_normalize_scales_linearly():
    assert normalize((175.0,), axis_range=350.0) == (0.5,)


def test_radial_deadzone_zeroes_small_vector():
    assert radial_deadzone((0.05, 0.02), deadzone=0.08) == (0.0, 0.0)


def test_radial_deadzone_passes_large_vector_through_rescaled():
    out = radial_deadzone((1.0, 0.0), deadzone=0.08)
    assert out[0] == pytest.approx(1.0)
    assert out[1] == pytest.approx(0.0)


def test_radial_deadzone_preserves_direction_on_diagonal():
    # Equal-magnitude diagonal push must not collapse to a single axis.
    x, y = radial_deadzone((0.3, 0.3), deadzone=0.08)
    assert x == pytest.approx(y)
    assert x > 0


def test_radial_deadzone_disabled_when_zero():
    assert radial_deadzone((0.01, 0.02), deadzone=0.0) == (0.01, 0.02)


def test_expo_curve_preserves_sign_and_zero():
    out = expo_curve((0.5, -0.5, 0.0), gamma=2.0)
    assert out == pytest.approx((0.25, -0.25, 0.0))


def test_expo_curve_gamma_one_is_identity():
    out = expo_curve((0.3, -0.7), gamma=1.0)
    assert out == pytest.approx((0.3, -0.7))


def test_dominant_axis_suppress_zeroes_weaker_axis():
    out = dominant_axis_suppress((1.0, 0.1), ratio=4.0)
    assert out == (1.0, 0.0)


def test_dominant_axis_suppress_keeps_comparable_axes():
    out = dominant_axis_suppress((1.0, 0.9), ratio=4.0)
    assert out == (1.0, 0.9)


def test_dominant_axis_suppress_disabled_when_ratio_zero():
    assert dominant_axis_suppress((1.0, 0.1), ratio=0.0) == (1.0, 0.1)


def test_ema_smoother_converges_toward_constant_input():
    smoother = EmaSmoother(alpha=0.5, size=1)
    for _ in range(20):
        (value,) = smoother.apply((1.0,))
    assert value == pytest.approx(1.0, abs=1e-4)


def test_ema_smoother_starts_from_zero():
    smoother = EmaSmoother(alpha=0.3, size=2)
    out = smoother.apply((1.0, -1.0))
    assert out == pytest.approx((0.3, -0.3))


def test_ema_smoother_reset_clears_history():
    smoother = EmaSmoother(alpha=0.5, size=1)
    smoother.apply((1.0,))
    smoother.reset()
    (value,) = smoother.apply((0.0,))
    assert value == 0.0


def test_ema_smoother_rejects_invalid_alpha():
    with pytest.raises(ValueError):
        EmaSmoother(alpha=0.0, size=1)
