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

The agent owns the check → repair → recheck → retry workflow. A failed
preflight is a diagnostic for you to act on, not a reason to hand installation
commands back to the user. Perform routine dependency repairs within the
user's authorization, using the environment's permission mechanism when needed.
Ask the user only if a permission denial or another concrete blocker prevents
you from continuing. Do not stop after merely suggesting an update.

Run the scripts from this skill's actual installation directory. In PowerShell,
set `$skillRoot` to that directory (the directory containing this `SKILL.md`).
Before a URL download, run:

```powershell
python "$skillRoot\scripts\setup.py" --check --check-updates
```

For local video files, omit `--check-updates` to avoid the network check.

- Exit `0`: dependencies found; with `--check-updates`, the installed yt-dlp
  is at least as recent as the latest stable release reported by GitHub.
- Exit `2`: a dependency is missing. The online preflight also requires Deno,
  yt-dlp's default JavaScript runtime for YouTube challenges. Run:

```powershell
python "$skillRoot\scripts\setup.py" --install
```

The installer uses `winget` and `pip --user`. It installs missing tools,
including Deno, but does not upgrade an existing yt-dlp installation.
Tesseract is detected on PATH or in standard Windows installation folders;
preflight and OCR use the same discovery code.

- Exit `3`: yt-dlp is older than the latest stable release. Update it using
  its installation method, then rerun preflight. For this skill's Winget
  installation, use `winget upgrade --id yt-dlp.yt-dlp -e`. For a pip-managed
  installation, use its Python interpreter with
  `python -m pip install --upgrade "yt-dlp[default]"`. A standalone release
  executable supports `yt-dlp --update`. Check the executable path printed by
  preflight so the update targets the copy the skill actually uses.
- Exit `4`: freshness is unverified (for example, no network, GitHub rate
  limiting, or a non-stable version string). Diagnose the cause. If sandbox
  networking blocked the check, retry through the environment's network
  permission mechanism. For rate limits or non-stable builds, use the
  installation method's updater to check for updates. Do not describe an
  unverified downloader as up to date.

After installing or updating, rerun the same preflight command and verify the
resolved executable is the updated copy. Refresh the process PATH if an
installer changed it. Once preflight passes, run the orchestrator below;
if it previously failed, retry the user's original source and options.
Keep repairs targeted to the failed dependency. Do not loop indefinitely:
if a repair and recheck produce the same failure, investigate a different
evidence-based cause or report the concrete blocker and what you tried.

yt-dlp is a Python application, not an npm package; do not use `npx` to run it.
Keep tools installed outside the repository. Do not commit executables or
pin a release version in the skill.

A current downloader does not guarantee YouTube access. If a download still
returns HTTP 403, inspect yt-dlp's verbose diagnostics, including JavaScript
runtime / challenge-solver warnings. Repair the identified cause and retry.
For pip installations, the `yt-dlp[default]` extra supplies the challenge
solver; official release executables bundle it. If current stable still
fails, consult upstream troubleshooting before choosing another repair.
Do not bypass access controls or use browser cookies without user authorization.
If recovery remains blocked, explain the actual failure and attempted fixes;
do not claim the video was watched when downloading failed. See the upstream
[update instructions](https://github.com/yt-dlp/yt-dlp#update) and
[YouTube JavaScript requirements](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

### 2. Run the orchestrator

```powershell
python "$skillRoot\scripts\watch.py" "<url-or-path>" [--start MM:SS] [--end MM:SS] [--max-frames N]
```

The script prints a single-line JSON manifest on stdout, e.g.:

```json
{"workdir": "<temporary-directory>\\watch-abcd1234",
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
- All paths are passed as argument lists — spaces in user directories and
  `Program Files` work without manual quoting.

## Credits

Design borrows from [bradautomates/claude-video](https://github.com/bradautomates/claude-video)
(frame budgeting, captions-first transcription, exit-code preflight). This
skill is a Windows-first rewrite that swaps the cloud Whisper API for local
`faster-whisper` and adds `pytesseract` OCR for on-screen text.
