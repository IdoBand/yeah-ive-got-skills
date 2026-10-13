"""Shared executable discovery for preflight and OCR."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_binary(name: str) -> str | None:
    executable = shutil.which(name) or shutil.which(name + ".exe")
    if executable or name != "tesseract":
        return executable

    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Tesseract-OCR" / "tesseract.exe",
    ]
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Tesseract-OCR" / "tesseract.exe")
    return next((str(path) for path in candidates if path.is_file()), None)
