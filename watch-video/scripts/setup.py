"""Preflight + installer for the watch-video skill.

Exit codes:
    0  all dependencies present
    2  one or more dependencies missing (with --check)
    1  install failed (with --install)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

BINARIES = ["yt-dlp", "ffmpeg", "tesseract"]
PY_PACKAGES = ["faster_whisper", "pytesseract", "PIL"]

WINGET_IDS = {
    "ffmpeg": "Gyan.FFmpeg",
    "yt-dlp": "yt-dlp.yt-dlp",
    "tesseract": "UB-Mannheim.TesseractOCR",
}


def find_binary(name: str) -> str | None:
    return shutil.which(name) or shutil.which(name + ".exe")


def check_python_pkg(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def cmd_check() -> int:
    missing: list[str] = []
    for b in BINARIES:
        if not find_binary(b):
            missing.append(f"binary:{b}")
    for p in PY_PACKAGES:
        if not check_python_pkg(p):
            missing.append(f"python:{p}")

    if missing:
        print("MISSING: " + ", ".join(missing), file=sys.stderr)
        return 2
    print("OK: all dependencies present")
    return 0


def run(cmd: list[str]) -> int:
    print(">>> " + " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def cmd_install() -> int:
    if sys.platform != "win32":
        print("setup.py --install is Windows-only. Install yt-dlp, ffmpeg, "
              "tesseract, and the Python requirements manually.", file=sys.stderr)
        return 1

    failures: list[str] = []
    for binary, wid in WINGET_IDS.items():
        if find_binary(binary):
            print(f"skip {binary}: already installed")
            continue
        rc = run(["winget", "install", "--id", wid, "-e",
                  "--accept-source-agreements", "--accept-package-agreements"])
        if rc != 0:
            failures.append(f"winget:{wid}")

    rc = run([sys.executable, "-m", "pip", "install", "--user",
              "faster-whisper", "pytesseract", "Pillow"])
    if rc != 0:
        failures.append("pip:requirements")

    if failures:
        print("INSTALL FAILED: " + ", ".join(failures), file=sys.stderr)
        return 1

    print("Install complete. Open a new shell so PATH picks up new binaries, "
          "then re-run --check.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--install", action="store_true")
    args = ap.parse_args()
    return cmd_check() if args.check else cmd_install()


if __name__ == "__main__":
    sys.exit(main())
