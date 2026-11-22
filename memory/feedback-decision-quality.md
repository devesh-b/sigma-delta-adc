---
name: feedback-decision-quality
description: Lessons for sound coordinator decisions; full list in work/v1-design/STATE-2026-11-14.md §2
metadata:
  type: feedback
---
Before reporting or deciding, check that the bench can fail and that the result file actually holds data.

Things that have looked like design results but were not:
- latched benches (D62 → D63);
- silent transient-op fallback;
- non-physical .dc solutions;
- "empty netlist", which really means a timestep abort;
- empty output files from relative paths.

Rules that are stricter than the physics go to the user to redefine (D80, D83, D86); I never loosen a gate myself. PnR changes go in one at a time, with every check re-run, and reverted if worse. Cross-block budgets are re-checked when a block changes: fast-mode current, the x2 swing, the comparator CM kick, vg leakage.

**Why:** user (2026-11-14): "save context to a file, we need to ensure you make good decisions".

**How to apply:** read the state snapshot (`work/v1-design/STATE-*.md`) after any interruption, and refresh it at milestones. Related: [[feedback-green-is-not-proof]], [[feedback-agent-resume-vs-new]].
