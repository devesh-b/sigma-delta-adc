# v1-design agents ledger (2026-11-07, after S0–S2)

| Agent | Role | State |
|---|---|---|
| reviewers (Opus) | SPEC/PLAN, S1/S2, WO-01 (pd-expert) | DONE (REVIEW-*.md) |
| coders (Sonnet) | WO-01, WO-01a, WO-02, WO-03, WO-04 | DONE, all accepted |
| testers (Haiku) | acceptance WO-01/02, 01a, 03, 04 | DONE (results/ACCEPT-S0-S2-2026-11-07.md) |

| coder WO-05 (Sonnet) | S3 error budget → per-block specs | DONE: a3f590f, 6f1476b, d3fdf8b; joint 0.935 µV @15 SPS, 3.41 ppm; specs in results/s3_budget.md |
| Haiku tester | acceptance WO-05 @446cc9c | DONE 4/4 PASS (row 3 read by coordinator) — S3 CLOSED |
| reviewer (Opus) | design review of S3 | DONE → REVIEW-S3-2026-11-07.md; corrected table in SPEC §3.0 |

Next after WO-05: Haiku acceptance + design review, then SPEC §3 update, then S4 (corner-aware tier 0).
| coder WO-06 (Sonnet) | S4 corner model + hooks | RUNNING, budget 90 |
| coder WO-07 (Sonnet) | S5 tier-1 ngspice | RUNNING, budget 90 |
