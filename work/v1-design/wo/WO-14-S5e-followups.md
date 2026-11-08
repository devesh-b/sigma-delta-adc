# WO-14 (S5e follow-ups): gm-boost realism, V4 margin point, S3 attribution, small fixes

Coordinator-written, 2026-11-08. **Tier: routine (Sonnet).**
**Spec source:** REVIEW-S5e-2026-11-08.md (C-M1, C-M2, m1–m6) and DECISIONS D39.
Read `work/v1-design/HANDOFF.md` first, including the section **sandbox runs without the rta-tt lock**. Use direct `ssh sandbox` + nohup with the full env.

**Sandbox load rule.** The box is shared and another project currently loads it at about 6 on 6 cores.
- Before any sim, check `uptime`.
- Start only if the 1-minute load is below 4.
- Never run more than 2 of your processes at once. Use nice -n 10 and timeout.
- If the load stays at 4 or above for 30 min, stop and report. Do not wait in a poll loop longer than that.

## Files you may touch (nothing else)
- `design/tier1/gen_tier1.py`
- `design/tier1/tier1_tb.py`
- `design/tier1/decks/gmid_*.sp` (new)
- `design/params.py`
- `design/tests/test_tier1.py`
- `model/studies/s4_corners.py`
- `model/tests/test_s4_corners.py`
- `work/v1-design/results/s5f_tier1.md` (new)
- `work/v1-design/results/gmid_table.{md,json}` (new)
- `work/v1-design/results/s3_ab.md` (new)
- `work/v1-design/results/s5e_tier1.md`: relabel only, see item 7

## Items
1. **gm/Id table (C1 learning step).**
   - Devices: sky130A `pfet_g5v0d10v5` and `pfet_01v8`. Use L 1 µm and 2 µm.
   - Corners: tt/ss/ff × −40/27/100/125 °C.
   - Method: DC sweep of Vsg at |Vds| 0.5 V, using `.option gmin=1e-18` (the default gmin corrupts low currents).
   - Output: gm/Id against Id/(W/L).
   - From the table, at the worst corner for each device, compute gm(×k)/gm(base) for:
     - OTA1: base gm/Id 10, k = 2;
     - OTA2: base gm/Id 14 and 17, k = 1.5 and 2.
   - Write `results/gmid_table.{md,json}`.
2. **Separate the gm boost from the current boost (C-M1).**
   - Add per-OTA knobs `bstgm1` / `bstgm2` to `gen_tier1.py` (lines 244, 251). The default equals `bst`, so existing results stay bit-identical; add a test for that.
   - Rerun V5(i) at 4 MHz (OTA1 ×2, OTA2 ×1.5, N 256 and 1024) with the gm ratios from item 1 (worst corner, pfet_g5v0d10v5).
   - Use OTA2 base GBW 15 and 20 MHz, plus one OTA2 ×2 row.
   - Report INL against the targets (N 1024 ≤ 5 ppm, N 256 ≤ 20 ppm).
   - Also report the base gm/Id that OTA2 needs to reach boosted loaded GBW ≥ 22.5 MHz.
   - **Non-vacuity:** the row with `bstgm = bst` must reproduce the s5e value of 3.7 ppm at N 1024 / GBW2 15 within 2 %. The row with gm ratio 1.0 must FAIL the N 1024 target.
3. **V4 margin point (m2).** 2 MHz, N 4096, OTA1 12.5 V/µs, OTA2 SR 10.8 V/µs (= 13.5/1.25). Expect INL ≤ 1.333 ppm, which shows the 25 % margin.
4. **S3 attribution (m1).**
   - Run `model.studies.s3_budget` with the *current* script against `model/iadc.py` from a3ea4eb^ and from a3ea4eb. Use a temporary copy in `/home/mempool/regr/tt/WO-14/ab/`, never in the tree.
   - Record the joint INL and gain in `results/s3_ab.md`, separating the script change (af85d1e) from the Ck fix.
5. **Order-1 residue frame (m4).** Add the order-1 case to `_pair_error` / `test_residue_frame_*`. It must fail on the old frame.
6. **`fast_task` constants (m3).** Derive β2 from params, including Cp,vg (expect ≈ 0.497), and OTA2 boosted SR 20.25 V/µs (option A, D39). No hand literals.
7. **s5e relabel (C-M2, m5, m6).**
   - V5(ii) becomes "explained: OTA1 slew-limited at 3 MHz, option dominated by V5(i) and dropped (D39)". Fix the "option (a) unboosted" wording.
   - Add the note that the xcheck covers only the legacy OTA.
   - Add the sys-on CMRR per-point (≈ 165–170 dB) and silicon figures.
   - Do not run the 3 MHz point.

## Acceptance (Haiku or coordinator, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest model/tests design/tests -q` | pass |
| 2 | gm/Id deck | table written; values within the physical bound gm/Id < 1/(n·UT) at every row |
| 3 | `tier1_tb.py --fast3` (new mode, items 2–3) | run-health ACCEPT; non-vacuity rows behave as stated |
| 4 | `s3_ab` | both runs exit 0 |

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `design: gm/Id table decks + results`
2. `design: separate gm boost from current boost, fast3 mode (V5 rerun, V4 margin point) + tests`
3. `model: order-1 residue-frame test, fast_task constants from params`
4. `v1-design: S5f results, S3 A/B attribution, s5e relabel`

If `git commit` fails with a 1Password error, retry once, then report and stop.

## Budget and stop rule
At most 60 tool calls. Finish by reporting "k of 7 items done", with the INL table from item 2.
