---
name: feedback-workspace-in-tt
description: User wants ~/projects/tt used as the scratchpad and memory kept inside the tt folder
metadata:
  type: feedback
---

Use `~/projects/tt` as the working scratchpad for this project, not the session temp scratchpad. Keep memory files in `~/projects/tt/memory/`.

**Why:** The user said so explicitly and wants everything for the project in one place and portable.
**How to apply:** Put downloads, clones, sim outputs, and notes under `~/projects/tt/`. The Claude memory dir for this project is a symlink to `~/projects/tt/memory/`. See [[reference-tt-workspace]].
