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
| coder WO-06 (Sonnet) | S4 corner model + hooks | DONE: 88a4341, af85d1e, 7a822ab, d037e9d; REJECT: noise @15 SPS at fs 0.25 MHz/125 °C (2.98 vs 2.5 µV); all else passes, MC passes | user decision (0.25 MHz noise), then Haiku acceptance + review |
| coder WO-07 (Sonnet) | S5 tier-1 ngspice | DONE: f668cb4, 1c7655a, d826660 (committed by coordinator after 1Password unlock); null 4.6e-7, INL 0.29 ppm at spec OTA, 4 MHz needs GBW 20 MHz |
| Haiku tester | acceptance WO-07 @d826660 | DONE 5/5 PASS |
| reviewer (Opus) | design review of S5 | DONE → REVIEW-S5-2026-11-07.md; closable after S5b |
| coder WO-08 (Sonnet) | S5b tier-1 extensions (xcheck, A(v), loaded 2-pole OTA, real ref pins + D12 + CM, offsets + sys chop, R_src) | RUNNING, budget 100 |
| coder WO-06a (Sonnet) | S4 re-gate D27–D32 + CMRR axis | DONE e2915a0: all gates ACCEPT except CMRR sys-off 42.5 dB vs 60 (needs ε 0.1 %, have 0.75 % 3σ) — finding, owned by C4 topology; sys-on 143–166 dB (model hypothesis, WO-08 checks in SPICE) | wait WO-08, then S4 acceptance + review |
