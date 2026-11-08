# WO-13: model fixes (residue frame, Ck topology) + fast-mode option runs

Coordinator-written, 2026-11-08. **Tier: review.** Read `work/v1-design/HANDOFF.md` first (lock-free sandbox runs).
- The box has 6 cores: run at most 5 processes; s4 with `--procs 2`; tier1 one mode at a time.
- **Spec source:** `REVIEW-S5d-2026-11-08.md` (C1, M1, V1–V7, E2); DECISIONS D38.

## Files you may touch (nothing else)
- `model/iadc.py`
- `model/tests/*`
- `model/studies/s4_corners.py`
- `model/studies/s3_budget.py` (only if it needs the new `u_corr` API)
- `design/tier1/*`
- `design/tests/test_tier1.py`
- `work/v1-design/results/{s3_budget,s4_corners,s5e_tier1}.{md,json}`

## Items
1. **C1 residue frame.**
   - `iadc.convert` returns `st["u_corr"] = s·(u_mod + x2_final/(c1·c2·W))` (W = N(N−1)/2).
   - Delete `_corr`, the inline `corr` in `memory_uv`, and the MC inline line; use `u_corr` everywhere.
   - **V1:** a regression test where an ideal loop with sys pairs and input u + e·s reproduces the pair to ≤ 1e-12 at N 256/1024/4096. A copy of the old `_corr` must fail it. This replaces the "records the finding" test (V6).
   - The probe bounds become ≤ 1e-3 µV plus ε-scaling.
   - Drop the "metric floor (hypothesis)" label.
2. **M1 / D38(b) Ck topology.** In `iadc`:
   - the stage-2 sampled-cap term is c2·(1+k), derived from k and on by default (D25 separate k-DAC);
   - add `cp_hold1`/`cp_hold2` (default 0) that enter g only: p = (1 + (1+cp)/A)·g;
   - remove or rename the old `cp_vg` hook.

   This is **one dedicated commit**. In that commit, re-baseline the bit-identity regression, recording the old→new diff (max |Δu|, INL) in the commit message.
3. **Reruns for the record.** Run `s3_budget --out` and the full `s4_corners` + `--nonvac` (`--procs 2`).
   - Expect ≤ 3 % INL moves and the same verdicts.
   - Report the S4 sys-on, sys-pair offset and MC offset after the C1 fix (V2).
4. **V3 xcheck.**
   - The model side uses the new default. Gate deck/model INL at rel_sym ≤ 5 % (a tightening).
   - Add a nonvac copy with the Ck term removed that must REJECT.
   - Gate the A60_base_cpvg row with `cp_hold1` = 0.262 pF, expected within a few %. If it doesn't match, report it; don't widen the tolerance.
5. **V7.** Update the `fast_task` hand constants: β2 ≈ 0.55 with Ck; OTA2 SR 13.5 base / 27 boost.
6. **V4, deck.** 2 MHz, N 4096, OTA2 SR {11, 13.5} V/µs, OTA1 12.5, 11 DC points. Report the INL and the knee margin against 1.333 ppm.
7. **V5, deck, fast-mode options.** Same harness as `--knees4` R2. N 256 and 1024, 21 DC points.
   - (i) 4 MHz, boost both with **OTA2 boost ×1.5** (OTA1 12.5 → 25, OTA2 13.5 → 20.25 V/µs; GBW scaled ×2 and ×1.5).
   - (ii) 3 MHz, no boost, OTA1 12.5, OTA2 13.5, GBW1 ∈ {10, 16, 20} MHz × GBW2 ∈ {10, 15, 20, 25} MHz. Use a reduced grid if the run time is too long: GBW1 {16, 20} × GBW2 {15, 20}.
   - Report INL against the provisional targets (N 1024 ≤ 5 ppm, N 256 ≤ 20 ppm), and the current per the review's per-SR rule (OTA1 4.75 µA, OTA2 2.4 µA per V/µs, plus 26 µA).

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest design/tests model/tests -q` | pass (full env) |
| 2 | `s4_corners --out` / `--nonvac` | ACCEPT 0 / REJECT 1 |
| 3 | `s3_budget --out` | ACCEPT |
| 4 | `tier1_tb.py --xcheck` | ≤ 5 % rel_sym; ACCEPT |
| 5 | `tier1_tb.py --nonvac5` (no-Ck copy, old-`_corr` copy as a pytest) | REJECT |
| 6 | `tier1_tb.py --fast2` (V4 + V5) | tables; run-health ACCEPT |

## Commits (explicit paths, no trailer, no push)
1. `model: convert returns demodulated residue-corrected u (fix S4 sys-pair residue frame) + frame regression`
2. `model: stage-2 Ck loading from topology c2(1+k) default, cp_hold g-only term; re-baseline regressions`
3. `model: S3/S4 reruns after residue-frame and Ck fixes + results`
4. `design: tier-1 xcheck 5 % gate + no-Ck reject, fast-mode option runs (OTA2 boost 1.5, 3 MHz), N4096 OTA2 point + results`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget
At most 100 tool calls.
- Write the results md **as you go**, so they exist if your budget runs out.
- No interim reports.
- Finish with "k of 7 items done, with reasons".
- Don't relax anything; report SPEC-breaking findings.
