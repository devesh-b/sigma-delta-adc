# WO-12 (S5d): verification gaps from REVIEW-S5c-S4close

Coordinator-written, 2026-11-08. **Tier: review.** Read `work/v1-design/HANDOFF.md` first (lock-free sandbox runs). The box has 6 cores: run at most 5 processes, s4 with `--procs 2`, tier1 with its 3 internal threads, one tier1 mode at a time.
**Spec source:** `work/v1-design/REVIEW-S5c-S4close-2026-11-08.md` §7; DECISIONS D36, D37.

## Files you may touch (nothing else)
- `design/tier1/*`
- `design/tests/test_tier1.py`
- `model/studies/s4_corners.py`
- `model/tests/test_s4_corners.py`
- `model/iadc.py`: item 6 only; new behaviour default-off, regressions bit-identical
- `work/v1-design/results/s5d_tier1.{md,json}` (new)
- `work/v1-design/results/s4_corners.{md,json}`

## Items
1. **R4.** Restore the S4 sys-on asserts at N 4096. At N256, assert only an ε-independent bound (sys-on error ≤ 20 µV). Label the S4 sys-on column "metric floor (hypothesis)".
   - Run the review's probe: ε sweep at N 256 and N 1024, then with ideal A(v).
   - Report the 1/N² scaling and the ≈ 0 result with ideal A.
2. **R7.** In cm2, gate vg1,cm ∈ V_icm ± 0.15 V over Vin_cm 0.2–2.0 V. The no-D12 copy must REJECT on it, inside `--nonvac3` or a new `--nonvac4`.
3. **R6.**
   - Gate stage-2 island drift as well as stage 1.
   - Remove the invented 50 mV row (D37c).
   - Report both stages against the ±0.13 V CM step + drift budget. This is informational; the limit is set in C1.
4. **R1.** Re-derive the OTA1 SR knee against a slew INL share of 2 ppm, after the 1.5× margin: threshold 2/1.5 = 1.33 ppm.
   - Use the existing knees3 data. Add grid points {9.5, 10.5} V/µs at 2 MHz N256 and N1024 if the interpolation is too coarse.
   - Report the knee and the margin of 12 and 12.5 V/µs.
   - Also report the OTA2 knee at the same share, to support the review's OTA2 SR 13.5 V/µs proposal.
5. **R2.** Deck run at 4 MHz, N 256 and N 1024, 21 DC points:
   - OTA1 boosted (base SR 12.5);
   - OTA2 unboosted, SR 13.5 V/µs, loaded GBW ∈ {10, 15, 20, 25} MHz.
   - Report INL. The question is whether OTA2 GBW 20 MHz at base bias makes OTA1-only boost reach ≤ 5 ppm at N1024. This is fast-mode option (a).
6. **R9.** Find the cause of the 26–39 % deck-vs-model INL bias at constant A0. Suspect: the model β lacks Cp,vg 0.26 pF.
   - If the model lacks it, add an optional `cp_vg1`/`cp_vg2` (default off) to `iadc.py` and rerun xcheck with it on.
   - Report the bias before and after.
   - Don't change the 35 % tolerance.

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest design/tests model/tests -q` | pass, with the full env |
| 2 | `s4_corners --out <dir>` + `--nonvac` | ACCEPT exit 0 / REJECT exit 1; sys-on asserts at N 4096 |
| 3 | `tier1_tb.py --cm2` | ACCEPT, with the vg CM gate |
| 4 | `tier1_tb.py --nonvac3` (or `--nonvac4`) | no-D12 REJECTs on CM range; exit nonzero |
| 5 | `tier1_tb.py --drift` | both stages reported |
| 6 | `tier1_tb.py --knees4` (R1 + R2) | tables written; run-health ACCEPT |
| 7 | `tier1_tb.py --xcheck` | bias report before/after `cp_vg` |

## Commits (explicit paths, no trailer, no push)
1. `model: S4 sys-on asserts at N 4096, metric-floor label, probe (R4)`
2. `design: tier-1 vg CM gate + no-D12 reject, stage-2 drift (R7, R6)`
3. `design: tier-1 knees at slew INL share, OTA2 GBW fast-mode sweep (R1, R2)`
4. `model/design: Cp,vg in model beta, xcheck bias (R9) + results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget
At most 90 tool calls. No interim reports. Finish with "k of 6 items done, with reasons". Report any SPEC-breaking finding; don't relax anything.
