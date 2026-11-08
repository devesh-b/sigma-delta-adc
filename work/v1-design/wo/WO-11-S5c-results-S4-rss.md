# WO-11: S5c results write-up + S4 ε_eff combination per D36

Coordinator-written, 2026-11-08. **Tier: routine.** Read `work/v1-design/HANDOFF.md` first (lock-free sandbox runs). The sandbox has 6 cores: run ≤ 5 processes total, using `--procs 2` for s4.

## Files you may touch (nothing else)
- `work/v1-design/results/s5c_tier1.{md,json}` (new)
- `model/studies/s4_corners.py`
- `model/tests/test_s4_corners.py`
- `work/v1-design/results/s4_corners.{md,json}`

## Items
1. **S5c write-up.** The WO-09 logs are complete: `/home/mempool/regr/tt/WO-09/{knees3,cm2,drift,rsrc2,xcheck,nonvac3}.log` plus their output directories. Write `s5c_tier1.md` and `s5c_tier1.json` from them. Do not rerun anything.
   - Separated knee tables; margin of 12 V/µs over the OTA1 knee at 2 and 4 MHz; the OTA1-only-boost result.
   - The cm2 table on the slope metric. Label the old S5b CMRR numbers "superseded (m1)". State that the sign is confirmed as "−".
   - The drift table, including the FLAG: 0.25 MHz/N 4096 drift is 344 mV, above 0.2 V.
   - The rsrc2 finding (SPEC pad 179.6 dB; the review form is valid only for τ ≥ T).
   - The xcheck Roff 1e14 row: no change (0.410 vs 0.413 ppm), so m4's bias is not the null floor.
   - The nonvac3 results.
   - Give the exact commands used, from `/home/mempool/regr/tt/run_wo0910.sh`.
2. **D36 in s4_corners** (read DECISIONS D36):
   - ε_eff = ((Cp/Cs)·ε_Cs − ΔCp/Cs)/(1+Cp/Cs) + ε_inj.
   - MC: per-draw signed sum, with ε_inj at its worst sign against the draw.
   - 3σ corner rows: RSS of the two random terms + |ε_inj|.
   - Keep the hand-calc check (expect about 8.4e-4, about 61.5 dB, within 10 %). Show the D33 linear-sum value as "superseded (D36)".
   - The broken copies must still REJECT. If a copy no longer does (e.g. Cs 3 %), replace it with one that does and say why.
3. Rerun s4 and `--nonvac` (`--procs 2`, nohup) to `/home/mempool/regr/tt/WO-11/`. Expect ACCEPT, exit 0, and REJECT, exit 1.

## Commits (explicit paths, no trailer, no push)
1. `v1-design: S5c tier-1 results (separated knees, D12 residual, drift, pin path)`
2. `model: S4 eps_eff signed MC + RSS corner rows (D36) + results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget
At most 40 tool calls. No interim reports. Finish by reporting "k of 3 items done", with the gate lines.
