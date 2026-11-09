# WO-16 (S5h): solver convergence rule, re-verify margin-critical tier-1 results, fp2 window, W/L fix

Coordinator-written, 2026-11-09. **Tier: routine (Sonnet).** Spec source: REVIEW-S5g-2026-11-09.md (G-M1, G-M2, G-M3, Q1 minimal set), D43.
Read `work/v1-design/HANDOFF.md` first.

**Sandbox rules**
- Direct ssh + nohup, full env.
- Start only when the 1-minute load is below 4. Never more than **2** of your processes. nice -n 10, timeout.
- No wait loops based on pgrep (one matched its own command line in WO-15). Wait on a marker file.
- Give up after 30 min of high load.
- **Smoke-test every new mode on 1 job before launching the full set.**

## Files you may touch
- `design/tier1/tier1_tb.py`
- `design/tier1/gen_tier1.py`
- `design/params.py`
- `design/tests/test_tier1.py`
- `work/v1-design/results/s5h_tier1.md` (new)
- `work/v1-design/results/gmid_table.{md,json}`

## Items
1. **G-M2 fix.** `gmid_min_wl` must use the per-device current (I_tail/2).
   - The test must check per-device W/L against independent hand values: OTA1 ≈ 29, OTA2 ×2 ≈ 18, OTA2 ×1.5 ≈ 106 at L 1 µm, ±15 %.
   - The test must fail on the old I_tail convention.
   - Regenerate `gmid_table.{md,json}` from the existing CSVs. No new decks.
2. **Option ladder (D43c).**
   - Add `--opt O0|O1|O2` to tier-1 modes. O0 = current defaults. Each step divides reltol by 10, halves tmax and divides chgtol by 100. O2 also sets trtol 1. Add the floor tmax ≤ τ_cl/10.
   - Add `--method trap|gear`.
   - Add a helper that applies the acceptance rule: |Δ(O2−O1)| ≤ max(10 %·INL, 0.1·(gate − INL)); verdict on INL(O2)·(1 + |Δ|/INL).
   - Unit-test the helper, including one case where O0 → O1 fails the rule (non-vacuity).
3. **Minimal rerun set** (REVIEW-S5g Q1, about 30 jobs, 2 at a time):
   1. ladder characterisation on the s5f ×1.5 15 MHz N256 row, reltol and tmax separately (7 jobs), plus one trap-vs-gear pair;
   2. OTA2 knee, 2 MHz, N1024, SR2 12 / 13.5 / 15 at O1 and O2. N256 only at O2, informational (D43d);
   3. OTA1 knee, 2 MHz, N256 and N1024, SR1 9.5 / 10 / 10.5 at O2. Report the knee and the margin at 12.5 V/µs against the 25 % rule;
   4. V4 (11 V/µs) and V4m (10.8 V/µs), N4096, at O2;
   5. A′ rows (c) cold and (d) hot, N1024, at O2;
   6. T4 101-point, N1024 / 20 MHz, at O2: report whether the 5 ppm jagged cubic-fit residual shrinks;
   7. xcheck A60 base, one row at O1.
4. **fp2 window (G-M1).**
   - Sweep fp2_mult 1.5 / 2 / 3 / 4 / 6 / 10 / 30 on OTA1 only (OTA2 at 3), then on OTA2 only (OTA1 at 3).
   - Use the D39 boosted point, 4 MHz, N1024, at O1. Use O2 on the minimum and on the 30 point.
   - Report INL against fp2/GBW and the hand-predicted PM. Expect an OTA1 minimum near fp2/GBW ≈ 3.4.
   - Also run one T3 row (fp2×30) at O2, to confirm physics against numerics.

## Acceptance (coordinator, frozen copy)
| # | Row | Expect |
|---|---|---|
| 1 | pytest | pass, including the G-M2 hand-value test and the rule-helper non-vacuity test |
| 2 | ladder | O1→O2 passes the rule on every rerun row, or the row is reported as not converged |
| 3 | knees / V4 / A′ | verdicts restated at O2, with margins |

## Commits (explicit paths, no attribution trailer, no push)
1. `design: gm/Id min W/L per device (G-M2) + table`
2. `design: solver option ladder O0-O2, trap/gear, convergence-rule helper + tests`
3. `design: S5h reruns (knees, V4, A' at O2, fp2 window) + results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget
At most 60 tool calls. Report "k of 4 items done" with the O2 tables.
