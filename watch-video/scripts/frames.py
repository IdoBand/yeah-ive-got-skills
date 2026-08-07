"""ffmpeg frame extraction with duration-aware budgeting."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def probe_duration(video: Path) -> float:
    ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found on PATH (install ffmpeg)")
    out = subprocess.check_output([
        ffprobe, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(video),
    ])
    return float(json.loads(out)["format"]["duration"])


def compute_fps(duration_s: float, max_frames: int) -> float:
    """Cap at 2 fps and at max_frames total. Sparser for longer videos."""
    if duration_s <= 0:
        return 1.0
    fps = max_frames / duration_s
    return min(fps, 2.0)


def extract(video: Path, out_dir: Path, max_frames: int = 100,
            start: str | None = None, end: str | None = None,
            width: int = 1280) -> tuple[list[Path], float]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH")

    duration = probe_duration(video)
    if start or end:
        # Approximate window duration for fps calculation.
        def parse(t: str) -> float:
            parts = [float(p) for p in t.split(":")]
            while len(parts) < 3:
                parts.insert(0, 0.0)
            h, m, s = parts
            return h * 3600 + m * 60 + s
        s = parse(start) if start else 0.0
        e = parse(end) if end else duration
        window = max(0.5, e - s)
    else:
        window = duration

    fps = compute_fps(window, max_frames)
    pattern = str(out_dir / "frame_%04d.jpg")

    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    if start:
        cmd += ["-ss", start]
    cmd += ["-i", str(video)]
    if end:
        cmd += ["-to", end]
    cmd += [
        "-vf", f"fps={fps:.4f},scale={width}:-2",
        "-vframes", str(max_frames),
        "-q:v", "3",
        pattern,
    ]
    subprocess.run(cmd, check=True)

    frames = sorted(out_dir.glob("frame_*.jpg"))
    return frames, duration
