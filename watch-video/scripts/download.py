"""yt-dlp wrapper. Returns (video_path, captions_path_or_None)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def is_url(s: str) -> bool:
    return s.startswith(("http://", "https://", "www."))


def download(source: str, out_dir: Path) -> tuple[Path, Path | None]:
    out_dir.mkdir(parents=True, exist_ok=True)

    if not is_url(source):
        src = Path(source).resolve()
        if not src.exists():
            raise FileNotFoundError(src)
        dest = out_dir / src.name
        shutil.copy2(src, dest)
        # Look alongside source for a .srt with the same stem.
        for cand in (src.with_suffix(".srt"), src.with_suffix(".en.srt")):
            if cand.exists():
                dest_srt = out_dir / cand.name
                shutil.copy2(cand, dest_srt)
                return dest, dest_srt
        return dest, None

    ytdlp = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if not ytdlp:
        raise RuntimeError("yt-dlp not found on PATH")

    out_template = str(out_dir / "%(id)s.%(ext)s")
    cmd = [
        ytdlp,
        "--no-playlist",
        "--write-auto-subs",
        "--write-subs",
        "--sub-langs", "en.*,en",
        "--convert-subs", "srt",
        "-f", "bv*[height<=720]+ba/b[height<=720]/best",
        "--merge-output-format", "mp4",
        "-o", out_template,
        source,
    ]
    subprocess.run(cmd, check=True)

    videos = sorted(
        [p for p in out_dir.iterdir()
         if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}],
        key=lambda p: p.stat().st_mtime,
    )
    if not videos:
        raise RuntimeError("yt-dlp produced no video file")
    video = videos[-1]

    srts = sorted(out_dir.glob(f"{video.stem}*.srt"))
    captions = srts[0] if srts else None
    return video, captions
