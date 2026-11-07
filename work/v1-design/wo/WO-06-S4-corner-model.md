# WO-06 (S4): corner-aware tier 0 + model hooks from the S3 review

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer.
**Spec source:** SPEC.md §3.0 (per-block specs) and §6 (corners); PLAN.md S4; REVIEW-S3-2026-11-07.md task list; DECISIONS D13–D26.
Read `work/v1-design/HANDOFF.md` first.

## Files you may touch (nothing else)
- `model/iadc.py`
- `model/tests/` (new tests only)
- `model/studies/s4_corners.py` (new)
- `model/studies/s3_budget.py` (only the items named below)
- `work/v1-design/results/s4_corners.{md,json}` (new)

Don't touch `design/` (WO-07 owns it) or SPEC.md. New iadc fields must default to off, and the existing regression tests must stay bit-identical.

## Items
1. **iadc hooks** (REVIEW-S3 tasks):
   - (a) `a0_db2` and `a0_drop2`: separate OTA2 gain. Default = same as OTA1.
   - (b) `av_table1` / `av_table2`: an optional tabulated gain-vs-differential-output-voltage curve (V, dB) that replaces the quadratic drop when set. This is how Stage C feeds in simulated OTA curves.
   - (c) `r_ext_ref`: external DC resistance per reference pin. The reference-current term is I = fs·Cs·(VREF/2)·u² per pin, so the effective reference becomes VREF·(1 − 2·R·I/VREF) per conversion.
     - Theory check: INL ≈ 1.4 ppm at 10 Ω and ≈ 7 ppm at 50 Ω (review S3-7a), ±30 %.
   - (d) Inter-conversion memory: `reset_r` (fraction of final x1/x2 left after reset), carried across consecutive conversions in a batch run.
     - Theory check: offset 2·r·x1_prev/(c1(N−1)).
   - Tests for each, plus a broken copy that must fail each.
2. **s3_budget fixes:**
   - (a) The gate must REJECT any row whose value is set equal to its share. Test it with the old circular cap row.
   - (b) `--nonvac` writes md and json.
   - (c) Add the review's rows: reference current at R_ext 10 Ω → INL share 2 ppm; k/c1 ratio gain ≈ 11 ppm in place of the cap row; reset r ≤ 1e-4 with a 2-cycle window.
3. **S4 corner model (`s4_corners.py`).** Map each SPEC §6 point to bounding block parameters, using SPEC §3.0 limits as the worst case at the worst corner and nominal values at tt/27/3.3. No transistor data exists yet, so state the mapping as an explicit table:
   - A(0) and A(1.4 V) via `av_table`
   - en / sampled noise
   - fc
   - Vos1, Vos2 at 3σ (± signs)
   - comparator offset and noise
   - τ_in (Ron worst at ss/−40/3.0)
   - τ_ref
   - reset r
   - leakage (worst at ff/125/3.6)
   - kT/C at the actual temperature

   Run every precision-mode system spec at **all 63 analog PVT points** × fs {0.25, 2} MHz:
   - noise @15 and @240 SPS
   - INL (N 4096)
   - sys-pair offset
   - gain error
   - inter-conversion memory

   Plus an MC-style sweep: ≥ 200 draws of Vos1, Vos2, comparator offset, Cs+/Cs− mismatch (0.75 % 3σ → CMRR term) at tt/27, and ≥ 50 at the worst point.

   **Pass rule:** every spec passes at every point; for MC, μ ± 3σ inside the spec **and** every sample inside it. Print ACCEPT/REJECT with the failing point named.
4. **Fast mode (4 MHz):** report INL and noise at N 64/256/1024 with the hand slew-then-settle penalty noted. Propose its own INL target. This is informational; it is not gated.
5. **Non-vacuity:** a copy with A(1.4 V) = 60 dB at ss/125/3.0 must REJECT at that point. A copy with reset r = 1e-2 must REJECT the memory spec.

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest model/tests design/tests -q` | all pass; old regressions bit-identical |
| 2 | hook broken copies | each hook test fails |
| 3 | `python3 -m model.studies.s4_corners --out <dir>` | 63 × 2 PVT and the MC tables; ACCEPT, exit 0 |
| 4 | `s4_corners --nonvac` | REJECT naming ss/125/3.0 (INL) and memory; exit 1 |
| 5 | `s3_budget --out <dir>` | still ACCEPT with the new rows; old circular row REJECTs in a test |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `model: OTA2 gain, A(v) table, ref-pin R_ext, reset memory hooks (default off) + tests`
2. `model: s3_budget gate rejects value==share, nonvac writes files, review rows`
3. `model: S4 corner-aware tier 0 + results`

## Budget and stop rule
At most 90 tool calls. 63 × 2 points × several metrics is heavy: use `--bg`, parallelise with at most 4 processes (`nice -n 10`), and report the wall time. `rta-tt` is shared: retry on busy, and always `cd /home/mempool/tt-sd`. Use scp of specific files for results, not `--pull`. Finish by reporting "k of 5 items done, with reasons". If a spec fails at a corner, report it as a finding; don't relax it.
