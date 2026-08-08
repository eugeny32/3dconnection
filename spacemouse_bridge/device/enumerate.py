"""List all connected HID devices and print VID/PID/usage info.

This is the first diagnostic tool for the project (docs/PLAN.md, §3.1 / §6.2
task 2): it must be run against real hardware so the actual VID/PID and
report layout of the user's SpaceMouse can be captured. Nothing here is
hardcoded from memory -- we only annotate *known* 3Dconnexion/Logitech
vendor IDs as a hint, we never filter or assume a PID.
"""

from __future__ import annotations

import argparse
from typing import Any

import hid

# Known SpaceMouse vendor IDs, for display purposes only. Never used to
# filter devices or to assume a PID -- see CLAUDE.md ("не хардкодить PID").
KNOWN_VENDOR_IDS = {
    0x046D: "Logitech (legacy 3Dconnexion: SpaceNavigator/SpaceExplorer/SpacePilot)",
    0x256F: "3Dconnexion (SpaceMouse Wireless/Pro/Enterprise/Compact)",
}


def enumerate_devices() -> list[dict[str, Any]]:
    """Return the raw list of HID device descriptors from hidapi."""
    return hid.enumerate()


def format_table(devices: list[dict[str, Any]]) -> str:
    if not devices:
        return "No HID devices found."

    rows = []
    header = (
        "VID",
        "PID",
        "Usage Page",
        "Usage",
        "Manufacturer",
        "Product",
        "Path",
        "Note",
    )
    rows.append(header)
    for d in devices:
        vid = d.get("vendor_id", 0)
        pid = d.get("product_id", 0)
        note = KNOWN_VENDOR_IDS.get(vid, "")
        rows.append(
            (
                f"0x{vid:04X}",
                f"0x{pid:04X}",
                str(d.get("usage_page", "")),
                str(d.get("usage", "")),
                str(d.get("manufacturer_string") or ""),
                str(d.get("product_string") or ""),
                str(d.get("path") or ""),
                note,
            )
        )

    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    lines = []
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="spacemouse-bridge-enumerate",
        description="List all connected HID devices (VID/PID/usage page).",
    )
    parser.parse_args(argv)

    devices = enumerate_devices()
    print(format_table(devices))
    print()
    print(f"{len(devices)} device(s) found.")
    known = [d for d in devices if d.get("vendor_id") in KNOWN_VENDOR_IDS]
    if known:
        print(
            "Devices matching known 3Dconnexion/Logitech vendor IDs are marked "
            "in the Note column above -- copy their VID/PID into device_ids.toml."
        )
    else:
        print(
            "No device matched a known 3Dconnexion/Logitech vendor ID. "
            "If your SpaceMouse is plugged in, note its VID/PID from the "
            "table above manually."
        )


if __name__ == "__main__":
    main()
