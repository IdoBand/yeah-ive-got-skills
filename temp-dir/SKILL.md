---
name: temp-dir
description: Workflow for temporary files, logs, dumps, screenshots, etc. in a Git project.
---

Put temporary files in `temp/` at the project root; create it if needed, with a `.gitignore` containing `*` and `!/.gitignore` on separate lines so only the placeholder is trackable and all temporary contents are ignored.
