"""Run pytesseract over each frame and dump to frames_ocr.txt."""
from __future__ import annotations

from pathlib import Path

from dependencies import find_binary


def _ensure_tesseract_on_path() -> None:
    import pytesseract  # type: ignore

    executable = find_binary("tesseract")
    if not executable:
        raise RuntimeError("Tesseract not found on PATH or in standard installation folders")
    pytesseract.pytesseract.tesseract_cmd = executable


def _ts(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def run(frames: list[Path], duration_s: float, out_path: Path) -> int:
    _ensure_tesseract_on_path()
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore

    n = len(frames)
    if n == 0:
        out_path.write_text("", encoding="utf-8")
        return 0

    written = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for i, frame in enumerate(frames):
            t = (i / max(1, n - 1)) * duration_s if n > 1 else 0.0
            try:
                with Image.open(frame) as img:
                    text = pytesseract.image_to_string(img)
            except Exception as e:  # noqa: BLE001
                text = f"<ocr-error: {e}>"
            text = text.strip()
            # Skip near-empty results (a stray punctuation char isn't useful).
            if len(text) < 3:
                continue
            # Collapse to single line block, but keep newlines as " | " so it's grep-friendly.
            flat = " | ".join(ln.strip() for ln in text.splitlines() if ln.strip())
            fh.write(f"[t={_ts(t)}] [{frame.name}] {flat}\n")
            written += 1
    return written
