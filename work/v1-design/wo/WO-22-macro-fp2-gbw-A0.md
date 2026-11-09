# WO-22: macro and model scans for C1 (fp2 transfer, GBW for fast mode, boost A0 floor)

Coordinator-written, 2026-11-09. **Tier: routine (Sonnet).** Sources: REVIEW-C1a M2 and P1, D51, SPEC CL-1, `results/s5h_tier1.md` §5 (fp2 window), `design/tier1/gen_tier1.py` (OTA macro l.241–274), `design/tier1/tier1_tb.py` (`--point`, `--opt`), `model/iadc.py` (A0 / A(v) table hooks).

**Sandbox:** no load gate, at most 2 processes, nice and timeout. **Delete each raw csv right after its json is written.** Run from a frozen copy `regr/tt/WO-22-<sha>`. No shell wait loops: use a runner with a done marker, and report if a job is not finished when you check.

## Items
1. **(a) Single-pole GBW sweep.**
   - Point: the D39 / A′ boosted point at 4 MHz, N 1024, m 21, O1.
   - Sweep OTA1 GBW over {20, 22, 24, 26, 28, 30} MHz at **fp2_mult1 = 10 and 30** (the real OTA sits at 10–12). OTA2 at the A′ values, with fp2_mult2 = 3.
   - Report INL against GBW for each mult. Find the GBW where INL ≤ 5/1.5 ppm.
   - Rerun at O2 for the two points that bracket the crossing.
2. **(b) Pole-after-tanh macro.**
   - Add a gen_tier1 option `fp2_after1` / `fp2_after2` (default off, so behaviour is unchanged) that places the Rf/Cf second pole **after** the tanh stage, as in a folded cascode.
   - Unit test: default deck byte-identical; option on changes the deck as intended.
   - Run mult {2, 3, 4, 10} at GBW 20 MHz (same point, O1) and compare against S5h pole-before (10.9 / 3.29 / 8.06 / 21.0 ppm).
   - Say whether the low-mult optimum transfers.
3. **(c) Tier-0 A0 scan for the CL-1 floor.**
   - Using the model with finite OTA1 A0 (and the A(v) drop shape used in S4), compute INL against A0 ∈ {60, 64, 68, 72, 76, 80} dB at N 1024 (fast mode). Do the same at N 4096 for the precision cross-check (expect ≈ 5.2 ppm at the S4 point).
   - A_floor = the lowest A0 with INL ≤ 5/1.5 ppm at N 1024. Apply both A0 and A0 − 5 dB for A(v), as in CL-1.
4. **Results:** `work/v1-design/results/c1_macro_scans.md` with the tables, the GBW needed per mult, the transfer verdict for (b), and A_floor.

## Commits (explicit paths, no attribution trailer, no push)
1. `design: gen_tier1 fp2-after-tanh option + test`
2. `v1-design: C1 macro scans (single-pole GBW, pole order, boost A0 floor)`

## Budget
At most 40 tool calls. Report GBW_needed at mult 10 and 30, the pole-order verdict, and A_floor.
