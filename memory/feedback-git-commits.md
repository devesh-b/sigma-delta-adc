---
name: feedback-git-commits
description: User rules for git — atomic commits as you go, untested OK, no attribution trailers, push/PR only on explicit OK
metadata:
  type: feedback
---

Make atomic commits as you go, without being asked: the smallest functional change is one commit, in the order change → test → docs. Untested commits are fine when verification is slow. The commit body explains why, with evidence. Never add attribution trailers (Co-Authored-By, "Generated with", session links). Stage by explicit path only; never use `git add -A` or `git stash`. Push, PR, merge and force-push only on an explicit OK.

**Why:** These are user rules from AlphaOneSoC. Batching commits kills bisection, and trailers are unwanted.
**How to apply:** tt is not a git repo yet (2026-11-07). Apply these once a design repo exists. tt's `.claude/settings.json` blanks attribution. Repeat "no attribution trailer, no push" in every agent brief. See `WORKFLOW.md` §3 and [[feedback-tt-submission-repo]].
