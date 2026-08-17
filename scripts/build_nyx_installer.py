#!/usr/bin/env python3
"""Build a single-file Windows installer for Nyx.

This script is intentionally conservative: it packages the local runtime and
keeps the configuration in the working tree. The actual production installer
should be extended with signing, version metadata, and the full dependency set.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WORK = ROOT / ".nyx_build"
ENTRY = ROOT / "nyx.py"
DEFAULT_ICON = ROOT / "scripts" / "nyx_icon.ico"


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("Nyx Windows installer builds must run on Windows; PyInstaller is not a cross-compiler.")

    parser = argparse.ArgumentParser(description="Build a single-file Windows installer for Nyx.")
    parser.add_argument("--icon", default=str(DEFAULT_ICON), help="Path to a Windows .ico icon file.")
    args = parser.parse_args()

    icon_path = Path(args.icon)
    if not icon_path.is_absolute():
        icon_path = (ROOT / icon_path).resolve()
    else:
        icon_path = icon_path.resolve()

    if not icon_path.exists():
        if args.icon != str(DEFAULT_ICON):
            parser.error(f"Icon file does not exist: {icon_path}")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_nyx_icon.py")], check=True, cwd=str(ROOT))
        icon_path = DEFAULT_ICON.resolve()

    DIST.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console",
        "--name",
        "Nyx",
        "--icon",
        str(icon_path),
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
        str(ENTRY),
    ]

    subprocess.run(command, check=True, cwd=str(ROOT), env=env)
    print(f"Installer built in {DIST}")


if __name__ == "__main__":
    main()
