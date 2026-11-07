---
name: project-sandbox-incident-2026-11-07
description: The first tt sync deleted files in AlphaOneSoC's /home/mempool/tt on the sandbox; tt now lives in /home/mempool/tt-sd
metadata:
  type: project
---

On 2026-11-07 the first `scripts/sync-to-sandbox.sh` push targeted `/home/mempool/tt`. That dir already existed: it is AlphaOneSoC's TT tooling dir. Its `rsync --delete` removed files from `tt-support-tools` (191 tracked files), `venv`, `venv-26d`, `venv-precheck`, `venv-test`, and 59 `projects/*` hardening repos. Only their `.git` dirs survived, so committed content can likely be restored with `git restore`. Uncommitted content and any whole top-level entries that were deleted are lost. Evidence is in `/home/mempool/regr/tt/incident-2026-11-07/`. The user was told and repair is their call. The classifier blocked my attempt at `git checkout` in their tree.

**Why:** I assumed the remote dir was new without checking it. That broke the "look at the target before deleting or overwriting" rule.
**How to apply:** tt's tree on the box is `/home/mempool/tt-sd`, which holds a `.tt-sd-root` marker. Never write to `/home/mempool/tt`. Before any `--delete` or `rm` on the box, list the target and check who owns it. The sync script refuses non-empty dirs that lack the marker. See [[feedback-sandbox-only]].
