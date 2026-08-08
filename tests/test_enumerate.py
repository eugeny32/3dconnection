from spacemouse_bridge.device.enumerate import KNOWN_VENDOR_IDS, format_table

FAKE_DEVICES = [
    {
        "vendor_id": 0x256F,
        "product_id": 0xC635,
        "usage_page": 1,
        "usage": 8,
        "manufacturer_string": "3Dconnexion",
        "product_string": "SpaceMouse Compact",
        "path": b"/dev/hidraw0",
    },
    {
        "vendor_id": 0x046D,
        "product_id": 0x0100,
        "usage_page": 1,
        "usage": 2,
        "manufacturer_string": "Logitech",
        "product_string": "SpaceNavigator",
        "path": b"/dev/hidraw1",
    },
    {
        "vendor_id": 0x1234,
        "product_id": 0x5678,
        "usage_page": 1,
        "usage": 6,
        "manufacturer_string": "Some Keyboard Vendor",
        "product_string": "Generic Keyboard",
        "path": b"/dev/hidraw2",
    },
]


def test_format_table_empty():
    assert format_table([]) == "No HID devices found."


def test_format_table_marks_known_vendor_ids():
    table = format_table(FAKE_DEVICES)
    assert "0x256F" in table
    assert "0x046D" in table
    assert KNOWN_VENDOR_IDS[0x256F] in table
    assert KNOWN_VENDOR_IDS[0x046D] in table


def test_format_table_unknown_vendor_has_no_note():
    table = format_table([FAKE_DEVICES[2]])
    lines = table.splitlines()
    assert "0x1234" in lines[1]
    assert "0x5678" in lines[1]
