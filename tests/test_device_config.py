from spacemouse_bridge.device.config import DeviceId, load_device_ids


def test_load_default_device_ids_includes_spacemouse_pro():
    devices = load_device_ids()
    assert DeviceId(name="SpaceMouse Pro", vendor_id=0x046D, product_id=0xC62B) in devices


def test_load_device_ids_from_explicit_path(tmp_path):
    toml_path = tmp_path / "device_ids.toml"
    toml_path.write_text(
        '[[devices]]\nname = "Test Device"\nvendor_id = 0x1234\nproduct_id = 0x5678\n'
    )

    devices = load_device_ids(toml_path)

    assert devices == [DeviceId(name="Test Device", vendor_id=0x1234, product_id=0x5678)]
