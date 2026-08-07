---
name: watch-video
description: Download a video from a URL (YouTube, etc.) or local path, extract frames, transcribe speech (captions or local Whisper), and OCR on-screen text — then answer the user's question using both vision and text. Trigger when the user asks Claude to watch / analyze / summarize / quote from a video.
---

# watch-video (Windows-native)

Use this skill when the user pastes a video URL or local file path and wants Claude
to actually look at it — answer questions about what is said, what is shown,
or quote code that appears on screen.

## Workflow

### 1. Preflight

```
python "%USERPROFILE%\.claude\skills\watch-video\scripts\setup.py" --check
```

Exit code `0` means all dependencies present. Exit code `2` means one or
more of `yt-dlp`, `ffmpeg`, `tesseract`, or the Python packages are missing —
in that case run:

```
python "%USERPROFILE%\.claude\skills\watch-video\scripts\setup.py" --install
```

This uses `winget` and `pip --user` and may require user approval.

### 2. Run the orchestrator

```
python "%USERPROFILE%\.claude\skills\watch-video\scripts\watch.py" "<url-or-path>" [--start MM:SS] [--end MM:SS] [--max-frames N]
```

The script prints a single-line JSON manifest on stdout, e.g.:

```json
{"workdir": "C:\\Users\\USER\\AppData\\Local\\Temp\\watch-abcd1234",
 "video": "...\\download\\video.mp4",
 "captions": "...\\download\\video.en.srt",
 "frames_dir": "...\\frames",
 "frame_count": 42,
 "transcript": "...\\transcript.json",
 "ocr": "...\\frames_ocr.txt",
 "duration_seconds": 134.2}
```

### 3. Read the artifacts and answer

- Read all jpg files in `frames_dir` in parallel — Claude's vision handles them natively. Frame filenames are `frame_0001.jpg`, `frame_0002.jpg`, … and the manifest's `duration_seconds` lets you map index → timestamp (`t = (i-1) * duration / frame_count`).
- Read `transcript.json` — list of `{start, end, text}` segments in seconds.
- Read `frames_ocr.txt` — line-per-frame OCR dump prefixed with `[t=MM:SS]`. Use this to grep / quote exact on-screen text, especially code.

When citing, give the user a `MM:SS` timestamp.

### 4. Cleanup

When the user's question is fully answered, remove the working directory.
**Do not use `rm -rf`** — it does not exist in PowerShell. Use:

```
python -c "import shutil; shutil.rmtree(r'<workdir>')"
```

where `<workdir>` is the value from the manifest.

## Notes

- `--max-frames` defaults to 100; lower it to ~30 for very long videos to
  keep vision-token cost down.
- If the video has no captions, transcription falls back to local
  `faster-whisper` (`small`, int8 CPU). First run downloads the model
  (~250 MB) into `%USERPROFILE%\.cache\huggingface`.
- All paths are passed as argument lists — spaces in `C:\Users\...` and
  `Program Files` work without manual quoting.

## Credits

Design borrows from [bradautomates/claude-video](https://github.com/bradautomates/claude-video)
(frame budgeting, captions-first transcription, exit-code preflight). This
skill is a Windows-first rewrite that swaps the cloud Whisper API for local
`faster-whisper` and adds `pytesseract` OCR for on-screen text.
