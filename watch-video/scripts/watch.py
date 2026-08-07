"""watch-video orchestrator.

Usage:
    python watch.py <url-or-path> [--start MM:SS] [--end MM:SS] [--max-frames N]

Prints a single-line JSON manifest on stdout when complete.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

# Allow running as a script from any cwd.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import download as dl  # noqa: E402
import frames as fr  # noqa: E402
import ocr as ocr_mod  # noqa: E402
import transcribe as tr  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="Video URL or local file path")
    ap.add_argument("--start", default=None, help="Start time HH:MM:SS or MM:SS")
    ap.add_argument("--end", default=None, help="End time HH:MM:SS or MM:SS")
    ap.add_argument("--max-frames", type=int, default=100)
    ap.add_argument("--workdir", default=None,
                    help="Directory to use (default: a fresh tempdir)")
    args = ap.parse_args()

    work = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="watch-"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"workdir: {work}", file=sys.stderr, flush=True)

    print("[1/4] downloading...", file=sys.stderr, flush=True)
    video, captions = dl.download(args.source, work / "download")

    print("[2/4] extracting frames...", file=sys.stderr, flush=True)
    frame_paths, duration = fr.extract(
        video, work / "frames",
        max_frames=args.max_frames,
        start=args.start, end=args.end,
    )

    print("[3/4] transcribing...", file=sys.stderr, flush=True)
    segments, source = tr.transcribe(video, captions, work)
    transcript_path = work / "transcript.json"
    tr.write_transcript(segments, source, transcript_path)

    print("[4/4] OCR over frames...", file=sys.stderr, flush=True)
    ocr_path = work / "frames_ocr.txt"
    ocr_lines = ocr_mod.run(frame_paths, duration, ocr_path)

    manifest = {
        "workdir": str(work),
        "video": str(video),
        "captions": str(captions) if captions else None,
        "frames_dir": str(work / "frames"),
        "frame_count": len(frame_paths),
        "transcript": str(transcript_path),
        "transcript_source": source,
        "ocr": str(ocr_path),
        "ocr_lines": ocr_lines,
        "duration_seconds": duration,
    }
    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
