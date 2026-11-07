# WO-09 (S5c): tier-1 follow-ups from REVIEW-S4S5b

Coordinator-written, 2026-11-08. **Tier: review.** sd-adc-design-reviewer.
**Spec source:** `work/v1-design/REVIEW-S4S5b-2026-11-08.md` (C-M1, C-M3, C-M4, m1, m2, m3, m6, m7, m9); DECISIONS D12, D25, D31–D34; SPEC §3.0.
Read `work/v1-design/HANDOFF.md` first, including the **sandbox runs without the rta-tt lock** section. Use direct ssh + nohup for every run longer than a minute.

## Files you may touch (nothing else)
- `design/tier1/*`
- `design/params.py` (tier-1 constants only)
- `design/tests/test_tier1.py`
- `work/v1-design/results/s5b_tier1.md` (m7 text fix only)
- `work/v1-design/results/s5c_tier1.{md,json}` (new)

Do not edit `model/` (WO-10 owns it) or SPEC.md.

## Items
1. **Separated OTA knees (C-M1).**
   - Give OTA1 and OTA2 their own SR and GBW parameters in `gen_tier1.py`. Defaults: OTA1 at 12 V/µs and 10 MHz, OTA2 at its spec of 25 V/µs and 10 MHz. Boost scales both unless a flag says OTA1 only.
   - Sweep OTA1 SR with OTA2 at spec, then OTA2 SR with OTA1 at spec:
     - 2 MHz grid: {8, 9, 10, 11, 12, 13.5, 15} V/µs;
     - 4 MHz boost grid (base values): {9, 10, 11, 12, 13.5, 15};
     - N 256 and N 1024;
     - 21 DC points, symmetric slew.
   - Also run the 4 MHz case with **boost on OTA1 only** (OTA2 un-boosted at its base spec), N 1024.
   - Report each knee: the lowest SR with INL ≤ 1/1.5 of the 20 ppm budget, i.e. ≤ 13.3 ppm. Use the D28 fast-mode targets at 4 MHz. Give the margin of 12 V/µs over the OTA1-only knee.
   - This takes about 40–60 runs. At most 3 in parallel.
2. **CMRR metric (m1).**
   - Redefine CMRR as the slope across Vin_cm ∈ {0.2, 1.0, 2.0} V at **fixed** mismatch: |ΔVin_cm / ΔVoff|.
   - Sys off uses the plain offset. Sys on uses the pair-demodulated offset (the offset term, not the `pair_V` gain term).
   - Keep the old numbers in the md, labelled "superseded (m1)".
3. **D12 residual in the deck (C-M3, m2).**
   - Add Cp,top per side on the floating top-plate nodes, at {10, 20} fF.
   - Add ΔCp,top at {0, 0.25, 1} fF, with Cs mismatch ε_Cs at {0, 0.75 %}.
   - Derive the closed form for ε_eff, **including the sign** of the ΔCp/Cs and (Cp/Cs)·ε_Cs terms. The review writes it as "−" in C-M3 and "+" in §5. Settle which is right from the deck and state it.
   - Gate: deck vs closed form within 25 %.
   - Report sys-off and sys-on CMRR (item-2 metric) for each case.
   - **Broken copy:** ΔCp,top 2 fF must REJECT the 60 dB sys-off gate.
4. **Island CM drift (C-M4).**
   - Add a tier-1 case with the 1e12/1e13 bleeders removed (or raised to 1e16) and a 100 pA leakage source on each island node.
   - fs 2 MHz and 0.25 MHz; N 4096 if the run time allows, otherwise N 1024, extrapolated linearly and labelled as such.
   - Report the island CM drift against the closed form I·N/(fs·C_island) within 25 %.
5. **Pin-path CMRR (m6).**
   - An `--rsrc` case: Vin_cm sweep {0.2, 2.0} V with ΔR between VIN+ and VIN− of {0, 50} Ω, D12 on, Cp,top 15 fF, sys on.
   - Report sys-on CMRR against the closed form ≈ 1/(ΔR·fs·Cp,top), within 30 %.
6. **Xcheck floor (m3).** Rerun the xcheck A0 80 dB row at Roff 1e14. Report deck vs model.
7. **Text and labels (m7, m9).**
   - Fix the "floor-limited by bleeders" sentence in `s5b_tier1.md`: the term is second order (ε²).
   - Label the `--knees2` ACCEPT as "run-health ACCEPT" and print the spec FLAG count.
8. **Non-vacuity.** Each must REJECT:
   - the ΔCp 2 fF copy (item 3);
   - an OTA1-SR-6 V/µs copy at 2 MHz N 256 (item 1);
   - a leakage copy at 10 nA, whose drift exceeds 0.2 V at 0.25 MHz (item 4).

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest design/tests -q` | pass |
| 2 | `tier1_tb.py --knees3` (name it so) | separated knee tables; run-health ACCEPT; knees printed |
| 3 | `tier1_tb.py --cm2` | closed-form check within 25 %; CMRR table on the new metric; ACCEPT |
| 4 | `tier1_tb.py --drift` | drift vs closed form within 25 %; ACCEPT |
| 5 | `tier1_tb.py --rsrc2` | pin-path CMRR vs closed form within 30 %; ACCEPT |
| 6 | `tier1_tb.py --xcheck` | the A0 80 row at Roff 1e14; ACCEPT |
| 7 | `tier1_tb.py --nonvac3` | the three broken cases REJECT; exit nonzero |

Every ngspice run must pass the existing run checks (tstop, log scan, netlist audit).

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `design: tier-1 separate OTA1/OTA2 SR/GBW, separated knees (C-M1)`
2. `design: tier-1 CMRR slope metric, Cp,top/ΔCp D12 residual + closed form (m1, C-M3)`
3. `design: tier-1 island leakage drift, pin-path CMRR, xcheck Roff 1e14, labels + results`

If `git commit` fails with a 1Password error, retry once, then stop committing and report.

## Budget and stop rule
At most 100 tool calls. Run on the sandbox via direct ssh + nohup (HANDOFF), with `nice -n 10`, `timeout`, and at most 3 parallel ngspice processes. Never put poll loops inside rta-tt. Finish by reporting "k of 8 items done, with reasons". Report any finding that breaks a SPEC §3.0 row; don't relax anything.
