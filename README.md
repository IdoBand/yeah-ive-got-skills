# yeah-ive-got-skills

Agent Skills 

## [watch-video](watch-video/SKILL.md)

Frames, transcript, and OCR from a video URL or local file, so Claude answers
from both what's said and what's shown.

**Tech** — `yt-dlp`, `ffmpeg`, `tesseract`, `faster-whisper`, `pytesseract`, `Pillow`

**Credits** — design borrowed from [bradautomates/claude-video](https://github.com/bradautomates/claude-video) (MIT, © 2026 Bradley Bonanno); independent reimplementation, no upstream code reused.

## [create-mermaid-diagrams](create-mermaid-diagrams/SKILL.md)

Draws a workflow, architecture, sequence, or state machine as Mermaid in a `.md`
previewed in the editor.


## [migrate-to-codex](migrate-to-codex/SKILL.md)

Convert Claude Code projects to Codex, preserving shared instruction symlinks
and auditing references across skills and supporting files.

**Credits** — enhanced copy of OpenAI's [migrate-to-codex](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431/skills/.curated/migrate-to-codex), retaining its original name and [Apache 2.0 license](migrate-to-codex/LICENSE.txt). Local enhancements and pinned upstream version are documented in the skill.


## [temp-dir](temp-dir/SKILL.md)

Keep disposable working files in the Git project's root `temp/` directory,
with a tracked `.gitignore` that excludes temporary contents.
