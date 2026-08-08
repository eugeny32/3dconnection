from spacemouse_bridge.device.decoders import (
    ButtonReport,
    CombinedAxisReport,
    RotationReport,
    TranslationReport,
    decode_report,
)


def test_decode_translation_report():
    # Tx=300 (0x012C LE), Ty=-1, Tz=0
    data = bytes([0x2C, 0x01, 0xFF, 0xFF, 0x00, 0x00])
    report = decode_report(0x01, data)
    assert report == TranslationReport(tx=300, ty=-1, tz=0)


def test_decode_rotation_report():
    data = bytes([0x00, 0x00, 0x2C, 0x01, 0xFF, 0xFF])
    report = decode_report(0x02, data)
    assert report == RotationReport(rx=0, ry=300, rz=-1)


def test_decode_combined_new_generation_report():
    # 12-byte body: all six axes in one report ID 0x01.
    data = bytes(
        [0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x04, 0x00, 0x05, 0x00, 0x06, 0x00]
    )
    report = decode_report(0x01, data)
    assert report == CombinedAxisReport(tx=1, ty=2, tz=3, rx=4, ry=5, rz=6)


def test_decode_button_report():
    data = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00])
    report = decode_report(0x03, data)
    assert report == ButtonReport(buttons=1)


def test_decode_button_report_release_is_zero():
    data = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    report = decode_report(0x03, data)
    assert report == ButtonReport(buttons=0)


def test_decode_unknown_report_id_returns_none():
    assert decode_report(0x99, bytes([1, 2, 3])) is None


def test_decode_short_translation_report_returns_none():
    assert decode_report(0x01, bytes([0x00])) is None
