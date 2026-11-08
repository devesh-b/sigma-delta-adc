# WO-15 (S5g): boosted-operating-point runs, INL-vs-GBW2 trend, gm/Id tooling

Coordinator-written, 2026-11-09. **Tier: routine (Sonnet).** Spec source: REVIEW-S5f-2026-11-09.md (M2, m1, m2, m3, m5, m6, Q4).
Read `work/v1-design/HANDOFF.md` first, including the section **sandbox runs without the rta-tt lock**.

**Sandbox rules**
- Use direct ssh + nohup, with the full env.
- Start only when the 1-minute load is below 4.
- Run at most **2 of your processes** at once, including ngspice decks; never fan out wider. Use nice -n 10 and timeout.
- Give up after 30 min of high load and report.

## Files you may touch
- `design/tier1/tier1_tb.py`
- `design/tier1/gen_tier1.py`
- `design/tier1/decks/gmid_*.sp`
- `design/tests/test_tier1.py`
- `work/v1-design/results/s5g_tier1.md` (new)
- `work/v1-design/results/gmid_table.{md,json}`

## Items
1. **Cold-corner boosted point (M2).** New mode `--fast4`, 4 MHz, N 256 and 1024, `bstgm = bst` (absolute operating points):
   - (a) the D39 point: OTA1 20 MHz / 25 V/µs, OTA2 22.5 MHz / 20.25 V/µs (control; expect ≈ 3.7 ppm at N 1024);
   - (b) cold, option A: OTA1 30 MHz / 25, OTA2 34 MHz / 20.25;
   - (c) cold, option A′: OTA1 30 / 25, OTA2 34 / 27;
   - (d) A′ at the hot point: OTA1 20 / 25, OTA2 22.5 / 27.
   - Report INL against the targets.
2. **Trend discrimination (Q4)**, at 4 MHz, N 256 and 1024:
   - (1) ideal OTA1 (GBW1 1 GHz, SR1 1000 V/µs), GBW2 15 / 20 / 25 MHz at 20.25 V/µs;
   - (2) the 15 vs 20 MHz rows of s5f (×1.5 rows, gm ratio 1.283) at reltol 1e-5 and maxstep halved;
   - (3) the same two rows with fp2_mult 30;
   - (4) signed INL(u) over 101 points for those two rows, with the residual after a third-order fit (rms and max).
   - State which hypothesis (a / b / c of REVIEW-S5f Q4) the data supports.
3. **fp2 sensitivity (m3):** the item-1 (a) and (c) rows with the second pole held at the *base* gm (a new knob `fp2_fixed`; default off, bit-identical).
4. **gm/Id tooling (m1, m2, m5, m6).**
   - Add L = 0.35 and 0.5 µm to the decks. Add a W-bin check at W 2 / 5 / 20 µm, pfet_01v8 tt only.
   - Cross-check the numerical gm against `.op` BSIM gm at 3 points per device (≤ 2 % agreement).
   - Add a monotonicity check on the strong-inversion side.
   - Add a broken copy (nfet model in a pfet deck, or a wrong column) that must REJECT.
   - Replace `need_22p5` with "minimum W/L meeting the boosted gm/Id target at every corner": OTA1 ≥ 10.05 at I_tail 35 µA, OTA2 ≥ 13.96 at 14.2 µA (×1.5) and ≥ 10.47 at 18.9 µA (×2). For each, report L, W/L and W·L.
   - Tighten the gm_ratio test to 1.474 ± 1 % and add a plateau-curve case.

## Acceptance (coordinator, frozen copy)
| # | Row | Expect |
|---|---|---|
| 1 | pytest | pass |
| 2 | `--gmid` | ACCEPT; the broken copy REJECTs |
| 3 | `--fast4` | run health ACCEPT; control (a) within 2 % of 3.686 ppm |

## Commits (explicit paths, no attribution trailer, no push)
1. `design: gm/Id L/W bins, op-gm cross-check, monotonicity + broken copy, boosted-point W/L target`
2. `design: fast4 mode (boosted operating points, trend discrimination, fp2 sensitivity) + tests`
3. `v1-design: S5g results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget
At most 60 tool calls. Report "k of 4 items done" with the item 1 and 2 tables.
