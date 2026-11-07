# WO-08 (S5b): tier-1 extensions from the S5 review

Coordinator-written, 2026-11-07. **Tier: review.** sd-adc-design-reviewer.
**Spec source:**
- `work/v1-design/REVIEW-S5-2026-11-07.md` (M1–M4, m1–m6)
- SPEC.md §3.0
- DECISIONS D12, D18, D24, D25
- S2 closed forms in `model/studies/s2_theory.py`

Read `work/v1-design/HANDOFF.md` first.

## Files you may touch (nothing else)
- `design/tier1/*`
- `design/params.py`: rename `SPICE_OPTIONS` → `SPICE_OPTIONS_TIER1`, update its users, add tier-1 constants
- `design/tests/test_tier1.py`
- `work/v1-design/results/s5_tier1.md` (text fixes) and `s5b_tier1.{md,json}` (new)

**Do not edit `model/`.** You may *import* `model/iadc.py`, but only for the item-1 cross-check table, which compares implementations. Theory remains the pass criterion everywhere else.

## Items
1. **Cross-check table (M1).** Deck vs model at matched settings, everything ideal except A0. Cases:
   - A0 60 dB at base;
   - A0 60 dB with k 0.25;
   - A0 60 dB with c1 0.25;
   - A0 80 dB at base.

   Record gain and INL for each. The reviewer's probe numbers (REVIEW-S5) are the expected values: gain within 5 %, INL within 35 %.

   **Noise transfer:** a trnoise source at OTA1's input, about 30 conversions, compared with the model's noise gain within 30 %. If ngspice trnoise makes this impractical, report why and propose a waiver.
2. **Text fixes (m1, m2).**
   - The gain error is ≈ −1.09·k/A0 (virtual-ground error × mean x1 = k·u), independent of c1.
   - The null floor comes from the reset-switch Roff: k/(Roff·fs·Cs1). Show it with Roff 1e14 (≈ 7e-9).
3. **SPICE_OPTIONS scope (m3).** Rename to `SPICE_OPTIONS_TIER1` and document the per-tier requalification rule in the README: a tier-2 null test with transistor switches over reltol {1e-3, 1e-4, 1e-5} × chgtol {1e-14, 1e-16}; the INL change must stay below 0.1× budget.
4. **A(v) in the deck (M2).**
   - A B-source nonlinear output conductance giving **static** A(x) = A0·max(0.02, 1 − drop·(x/vsw)²) (the same form as `_leaky`) on OTA1 and OTA2.
   - Run at drop 0.9 with vsw matched to the S3 point (vlin_diff 2.0 V), A0 80 dB.
   - Expect deck vs model INL within 30 %.
   - The README defines the A(v) table that C1 must deliver as static vo/vd.
5. **Load-dependent OTA (M3).**
   - Replace the ideal-output macromodel with gm into an output node: Ro, Cpar at the output and at the virtual ground (use β 0.84 per SPEC), a second pole at ≈ 3×GBW (PM ≈ 70°), and slew via a tail-current limit (asymmetric option).
   - Re-run the knees with 21 DC points at 2 and 4 MHz for GBW {5, 10, 20, 30} MHz and SR {6, 12, 25} V/µs.
   - The Cs2 hold-phase load (D25) must now be present.
   - Flag every knee above SPEC §3.0.
6. **Real reference pins and common mode (M4a).**
   - VREF+ = 2.048 V, VREF− = 0 V (D24).
   - Implement D12 top-plate shorting during sampling, as in D25.
   - Give the OTA macro a finite CM loop: CMFB gain 40 dB, bandwidth 10 MHz.
   - Sweep Vin_cm over {0.2, 1.0, 2.0} V.
   - Log the virtual-ground CM excursion (min/max per corner-free run) and the differential error vs Vin_cm (CMRR at an ideal Cs+/Cs− match, then with a 0.25 % mismatch).
   - Report the PMOS-pair input CM range those numbers require. That becomes the C1/C4 target.
7. **Offsets and system chop (m5).**
   - Inject Vos1 = Vos2 = 9 mV and a comparator offset of 20 mV.
   - Compare with the S2 closed forms: 2·Vos2/(c1(N−1)); the OTA-chop residual lf·Vos/(N−1) when OTA chop is modelled as an ideal input/output swap at fs/2 with the phase restarted each reset; and the order-1 lf·Vos/N path. Note that residue reconstruction hides the order-1 path, so for order 1 use the plain CoI output.
   - Then run sys-chop pairs (input swap at the pin side, reset between halves). The residual must be ≤ 0.5 µV equivalent.
8. **Source impedance (m6).** R_src ∈ {1 k, 10 k, 10 k + 10 nF at the pin} on VIN, with INL and gain at the spec OTA. Check the SPEC input-source row (≈ 1 kΩ without a board cap).
9. **Non-vacuity.** Each must REJECT:
   - an A(v) deck with drop 0.9 at vsw 0.8 V;
   - a sys-chop pair with the swap one cycle late, i.e. mid-conversion;
   - Vin_cm 2.0 V without D12 shorting, if the virtual-ground CM leaves the stated range (otherwise report it).

## Acceptance (Haiku, frozen copy)
| # | Command | Expect |
|---|---|---|
| 1 | `pytest design/tests -q` | pass |
| 2 | `tier1_tb.py --xcheck` | cross-check table within tolerance; ACCEPT |
| 3 | `tier1_tb.py --av` | deck vs model A(v) INL within 30 %; ACCEPT |
| 4 | `tier1_tb.py --knees2` | 21-point knee table written; flags listed |
| 5 | `tier1_tb.py --cm` | CM-excursion log + CMRR table written |
| 6 | `tier1_tb.py --offsets` | closed-form matches; sys-pair residual ≤ 0.5 µV; ACCEPT |
| 7 | `tier1_tb.py --rsrc` | table written |
| 8 | `tier1_tb.py --nonvac2` | the broken cases REJECT; exit nonzero |

Every ngspice run must pass the existing run checks (tstop, log scan, netlist audit).

## Commits (explicit paths, path-limited, no attribution trailer, no push)
1. `design: tier-1 text fixes, SPICE_OPTIONS_TIER1 scope, model cross-check`
2. `design: tier-1 A(v) output stage and load-dependent two-pole OTA, 21-point knees`
3. `design: tier-1 real reference pins, D12 CM-rejecting switching, CM log`
4. `design: tier-1 offsets and system-chop pairs, source-impedance sweep, non-vacuity + results`

If `git commit` fails with a 1Password error, retry once, then stop committing and report.

## Budget and stop rule
At most 100 tool calls. Use `--bg`, run at most 3 parallel ngspice processes, and wrap each in `nice -n 10` and `timeout`. `rta-tt` is shared: retry on busy, and always cd explicitly. Pull results by scp of specific files. Finish by reporting "k of 9 items done, with reasons". Report any finding that breaks a SPEC §3.0 row; don't relax anything.
