"""Entry point for the SpaceMouse Universal Bridge CLI.

--profile is added in a later task (see docs/PLAN.md, §6.2). --dump (task 3)
captures raw reports to JSONL; --viz (task 5) shows a live 6-axis terminal
visualization.
"""

import argparse
import sys

from spacemouse_bridge.app.viz import run_viz
from spacemouse_bridge.device.config import load_device_ids
from spacemouse_bridge.device.reader import HidReader, dump_to_jsonl


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="spacemouse-bridge")
    parser.add_argument(
        "--dump",
        metavar="OUT.jsonl",
        help="capture raw HID reports to a JSONL file until --duration elapses",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="seconds to capture with --dump (default: 10)",
    )
    parser.add_argument(
        "--viz",
        action="store_true",
        help="show a live 6-axis terminal visualization (Ctrl+C to stop)",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.dump:
        _run_dump(args.dump, args.duration)
        return

    if args.viz:
        _run_viz()
        return

    print("spacemouse-bridge: skeleton only, no functionality yet (see docs/PLAN.md)")


def _open_first_device() -> HidReader | None:
    devices = load_device_ids()
    if not devices:
        print("No devices configured in device_ids.toml -- run "
              "`python -m spacemouse_bridge.device.enumerate` and add one.")
        return None

    device = devices[0]
    print(f"Opening {device.name} (VID 0x{device.vendor_id:04X} "
          f"PID 0x{device.product_id:04X})...")
    return HidReader(device.vendor_id, device.product_id)


def _run_dump(out_path: str, duration_s: float) -> None:
    reader = _open_first_device()
    if reader is None:
        return
    with reader:
        print(f"Capturing for {duration_s}s -> {out_path}")
        count = dump_to_jsonl(reader, out_path, duration_s)
    print(f"{count} report(s) written.")


def _run_viz() -> None:
    reader = _open_first_device()
    if reader is None:
        return
    with reader:
        print("Ctrl+C to stop.")
        run_viz(reader)


if __name__ == "__main__":
    main()
