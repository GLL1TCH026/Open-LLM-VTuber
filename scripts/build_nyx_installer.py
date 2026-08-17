#!/usr/bin/env python3
"""Build a single-file Windows installer for Nyx.

This script is intentionally conservative: it packages the local runtime and
keeps the configuration in the working tree. The actual production installer
should be extended with signing, version metadata, and the full dependency set.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WORK = ROOT / ".nyx_build"
ENTRY = ROOT / "nyx.py"
DEFAULT_ICON = ROOT / "scripts" / "nyx_icon.ico"
LOG_PATH = ROOT / "build_nyx.log"


def _run_build(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    """Run the build command and persist the output to build_nyx.log."""
    result = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True, check=False)
    combined_output = (result.stdout or "") + (result.stderr or "")
    LOG_PATH.write_text(combined_output, encoding="utf-8")

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("Nyx Windows installer builds must run on Windows; PyInstaller is not a cross-compiler.")

    parser = argparse.ArgumentParser(description="Build a single-file Windows installer for Nyx.")
    parser.add_argument("--icon", default=str(DEFAULT_ICON), help="Path to a Windows .ico icon file.")
    parser.add_argument("--console", action="store_true", help="Keep the console window open for debugging.")
    args = parser.parse_args()

    icon_path = Path(args.icon)
    if not icon_path.is_absolute():
        icon_path = (ROOT / icon_path).resolve()
    else:
        icon_path = icon_path.resolve()

    if not icon_path.is_file():
        # If a user explicitly supplied a path that is not a regular file, reject it.
        if args.icon != str(DEFAULT_ICON):
            parser.error(f"Icon file does not exist or is not a file: {icon_path}")
        # For the default missing icon, generate a default safely and use it.
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_nyx_icon.py")], check=True, cwd=str(ROOT))
        icon_path = DEFAULT_ICON.resolve()

    DIST.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    hidden_imports = [
        "pycparser.lextab",
        "pycparser.yacctab",
        "tzdata",
        "scipy.special._cdflib",
    ]
    available_hidden_imports = []
    for module_name in hidden_imports:
        if importlib.util.find_spec(module_name) is not None:
            available_hidden_imports.extend(["--hidden-import", module_name])

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--noupx",
        "--onefile",
        "--console",
        "--name",
        "Nyx",
        "--icon",
        str(icon_path),
        *available_hidden_imports,
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
        str(ENTRY),
    ]

    _run_build(command, cwd=ROOT, env=env)
    print(f"Installer built in {DIST}")
    print(f"Build log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
