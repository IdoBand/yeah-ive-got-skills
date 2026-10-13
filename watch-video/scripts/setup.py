"""Preflight + installer for the watch-video skill.

Exit codes:
    0  all dependencies present
    2  one or more dependencies missing (with --check)
    1  install failed (with --install)
    3  yt-dlp update needed (with --check-updates)
    4  yt-dlp freshness could not be verified (with --check-updates)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request

from dependencies import find_binary

BINARIES = ["yt-dlp", "ffmpeg", "tesseract"]
PY_PACKAGES = ["faster_whisper", "pytesseract", "PIL"]

WINGET_IDS = {
    "ffmpeg": "Gyan.FFmpeg",
    "yt-dlp": "yt-dlp.yt-dlp",
    "tesseract": "UB-Mannheim.TesseractOCR",
    "deno": "DenoLand.Deno",
}


def check_ytdlp_update() -> int:
    executable = find_binary("yt-dlp")
    if not executable:
        print("MISSING: binary:yt-dlp", file=sys.stderr)
        return 2
    try:
        installed = subprocess.run(
            [executable, "--version"], check=True, capture_output=True,
            text=True, timeout=15,
        ).stdout.strip()
        request = urllib.request.Request(
            "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
            headers={"User-Agent": "watch-video-preflight", "Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            latest = json.load(response)["tag_name"]
        # Compare date components, not strings (zero padding may differ).
        if not all(re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}", value) for value in (installed, latest)):
            raise ValueError(f"Unrecognized stable version: installed={installed!r}, latest={latest!r}")
        outdated = tuple(map(int, installed.split("."))) < tuple(map(int, latest.split(".")))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(f"UNVERIFIED: yt-dlp update check failed: {exc}", file=sys.stderr)
        return 4
    print(f"yt-dlp: installed {installed}; latest stable {latest}; executable {executable}")
    if outdated:
        print("UPDATE NEEDED: update yt-dlp using its installation method, then rerun preflight.", file=sys.stderr)
        return 3
    return 0


def check_python_pkg(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def cmd_check(check_updates: bool = False) -> int:
    missing: list[str] = []
    for b in BINARIES + (["deno"] if check_updates else []):
        if not find_binary(b):
            missing.append(f"binary:{b}")
    for p in PY_PACKAGES:
        if not check_python_pkg(p):
            missing.append(f"python:{p}")

    if missing:
        print("MISSING: " + ", ".join(missing), file=sys.stderr)
        return 2
    print("OK: all dependencies present")
    return check_ytdlp_update() if check_updates else 0


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
    ap.add_argument("--check-updates", action="store_true",
                    help="With --check: require Deno and check yt-dlp against the latest stable release online")
    args = ap.parse_args()
    if args.check_updates and not args.check:
        ap.error("--check-updates requires --check")
    return cmd_check(args.check_updates) if args.check else cmd_install()


if __name__ == "__main__":
    sys.exit(main())
