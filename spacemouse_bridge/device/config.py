"""Load known device VID/PID entries from device_ids.toml.

Source of truth for which SpaceMouse identifiers the bridge knows about.
Nothing here is hardcoded in Python -- see CLAUDE.md ("не хардкодить PID").
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class DeviceId:
    name: str
    vendor_id: int
    product_id: int


def _default_toml_path() -> Path:
    return resources.files("spacemouse_bridge").joinpath("device_ids.toml")


def load_device_ids(path: Path | str | None = None) -> list[DeviceId]:
    """Parse device_ids.toml into a list of DeviceId entries."""
    source = Path(path) if path is not None else _default_toml_path()
    with open(source, "rb") as f:
        data = tomllib.load(f)

    return [
        DeviceId(
            name=entry["name"],
            vendor_id=entry["vendor_id"],
            product_id=entry["product_id"],
        )
        for entry in data.get("devices", [])
    ]
