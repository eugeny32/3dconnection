"""Entry point for the SpaceMouse Universal Bridge CLI.

Flags such as --dump, --viz and --profile are added in later tasks
(see docs/PLAN.md, §6.2). For now this only proves the package and
console-script entry point are wired up correctly.
"""

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="spacemouse-bridge")
    parser.parse_args(argv if argv is not None else sys.argv[1:])
    print("spacemouse-bridge: skeleton only, no functionality yet (see docs/PLAN.md)")


if __name__ == "__main__":
    main()
