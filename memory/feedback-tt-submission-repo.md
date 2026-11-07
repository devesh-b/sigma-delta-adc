---
name: feedback-tt-submission-repo
description: User rule — never commit in the public TT submission repo; leave changes uncommitted for the user; no Claude traces there
metadata:
  type: feedback
---

In the public TinyTapeout submission repo, don't commit at all. Leave changes uncommitted, back them up as a patch outside the repo, and let the user commit. Leave no trace of Claude there: no CLAUDE.md, `.claude/`, memory, claude.ai links, trailers, or "Claude"/"Anthropic" text. CI uses only TT's own tooling. Run a scrub grep before handing over.

**Why:** This is a user rule from AlphaOneSoC. The submission repo is public and should be the user's own work.
**How to apply:** Applies once tt has a shuttle repo. Keep the shell's cwd outside it and tell subagents not to write there. See `WORKFLOW.md` §12.
