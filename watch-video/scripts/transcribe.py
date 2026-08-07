"""Captions-first transcription, with local faster-whisper fallback."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

_SRT_TIME = re.compile(
    r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)"
)


def _srt_time_to_s(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    segments: list[dict] = []
    blocks = re.split(r"\r?\n\r?\n", text.strip())
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        time_line = next((ln for ln in lines if _SRT_TIME.search(ln)), None)
        if not time_line:
            continue
        m = _SRT_TIME.search(time_line)
        start = _srt_time_to_s(*m.group(1, 2, 3, 4))
        end = _srt_time_to_s(*m.group(5, 6, 7, 8))
        text_lines = [ln for ln in lines if ln is not time_line and not ln.isdigit()]
        # YouTube auto-captions repeat lines across cues; dedupe inside a cue.
        seen = []
        for ln in text_lines:
            ln = re.sub(r"<[^>]+>", "", ln).strip()
            if ln and ln not in seen:
                seen.append(ln)
        body = " ".join(seen).strip()
        if body:
            segments.append({"start": start, "end": end, "text": body})
    return segments


def _extract_audio(video: Path, out_wav: Path) -> None:
    ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found on PATH")
    subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(out_wav),
    ], check=True)


def whisper_transcribe(video: Path, work: Path) -> list[dict]:
    from faster_whisper import WhisperModel  # type: ignore

    wav = work / "audio.wav"
    _extract_audio(video, wav)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments_iter, _info = model.transcribe(
        str(wav), vad_filter=True, beam_size=1
    )
    return [
        {"start": float(s.start), "end": float(s.end), "text": s.text.strip()}
        for s in segments_iter
        if s.text and s.text.strip()
    ]


def transcribe(video: Path, captions: Path | None, work: Path) -> tuple[list[dict], str]:
    """Returns (segments, source) where source is 'captions' or 'whisper'."""
    if captions and captions.exists():
        segs = parse_srt(captions)
        if segs:
            return segs, "captions"
    return whisper_transcribe(video, work), "whisper"


def write_transcript(segments: list[dict], source: str, out: Path) -> None:
    out.write_text(
        json.dumps({"source": source, "segments": segments}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
